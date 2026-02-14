"""Repository quality checks executed against GitHub snapshot data."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
import yaml

from app.scanner.policy import RepoPolicy, apply_ignore_checks
from app.scanner.schemas import CheckResult, ExtensionMetric, ProjectMetrics

PINNED_SHA_RE = re.compile(r"^[a-fA-F0-9]{40}$")
USES_RE = re.compile(r"uses:\s*([A-Za-z0-9_.\-\/]+)@([^\s#]+)")
SECRET_PATTERNS = {
    "AWS Access Key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "GitHub Token": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "Google API Key": re.compile(r"AIza[0-9A-Za-z\-_]{20,}"),
}

OSV_QUERY_URL = "https://api.osv.dev/v1/querybatch"
MAX_DEPENDENCIES_FOR_OSV = 200
OSV_BATCH_SIZE = 100


@dataclass(frozen=True)
class DependencyRef:
    """Normalized dependency coordinate used for OSV lookups."""

    ecosystem: str
    name: str
    version: str


def _find_first_path(tree_paths: list[str], predicate: Callable[[str], bool]) -> str | None:
    """Return first path matching provided predicate."""

    for path in tree_paths:
        if predicate(path.lower()):
            return path
    return None


def detect_stacks(snapshot: Any) -> list[str]:
    """Infer primary technology stacks from repository tree."""

    tree = [path.lower() for path in snapshot.tree_paths]
    stacks: list[str] = []

    if any(path.endswith((".py", "pyproject.toml", "requirements.txt", "poetry.lock")) for path in tree):
        stacks.append("python")
    if any(
        path.endswith(("package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json"))
        for path in tree
    ):
        stacks.append("javascript")
    if any(path.endswith(("pom.xml", "build.gradle", "build.gradle.kts")) for path in tree):
        stacks.append("java")
    if any(path.endswith((".csproj", ".sln", "directory.build.props")) for path in tree):
        stacks.append("csharp")
    if any(path.endswith((".cpp", ".cc", ".cxx", ".h", ".hpp", "cmakelists.txt")) for path in tree):
        stacks.append("cpp")
    if any(path.endswith(("go.mod", ".go")) for path in tree):
        stacks.append("go")
    if any(path.endswith(("cargo.toml", "cargo.lock", ".rs")) for path in tree):
        stacks.append("rust")
    if any(path.endswith(("composer.json", "composer.lock", ".php")) for path in tree):
        stacks.append("php")
    if any(path.endswith(("gemfile", "gemfile.lock", ".rb")) for path in tree):
        stacks.append("ruby")
    if not stacks:
        stacks.append("unknown")
    return stacks


def project_line_metrics(snapshot: Any) -> ProjectMetrics:
    """Calculate scanned code lines/files grouped by file extension."""

    stats: dict[str, dict[str, int]] = {}
    total_lines = 0
    scanned_files = 0

    for path in snapshot.line_count_paths:
        content = snapshot.file_contents.get(path)
        if content is None:
            continue
        extension = _extension(path)
        lines = _count_lines(content)
        scanned_files += 1
        total_lines += lines
        bucket = stats.setdefault(extension, {"files": 0, "lines": 0})
        bucket["files"] += 1
        bucket["lines"] += lines

    by_extension = [
        ExtensionMetric(extension=ext, files=data["files"], lines=data["lines"])
        for ext, data in stats.items()
    ]
    by_extension.sort(key=lambda item: (-item.lines, item.extension))
    return ProjectMetrics(
        total_code_files=snapshot.line_count_candidates_total,
        total_code_lines=total_lines,
        scanned_code_files=scanned_files,
        sampled=snapshot.line_count_sampled,
        by_extension=by_extension,
    )


def docs_checks(snapshot: Any, readme_min_length: int = 200) -> list[CheckResult]:
    """Run documentation and license checks."""

    tree_paths = snapshot.tree_paths
    readme_path = _find_first_path(tree_paths, lambda p: p.split("/")[-1].startswith("readme."))
    readme_content = snapshot.file_contents.get(readme_path, "") if readme_path else ""

    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            id="readme_exists",
            name="README file exists",
            status="pass" if readme_path else "fail",
            details=f"Found at {readme_path}" if readme_path else "README file not found.",
            recommendation=None if readme_path else "Add a README.md with project overview and usage.",
        )
    )
    checks.append(
        CheckResult(
            id="readme_length",
            name="README length >= 200 chars",
            status="pass" if len(readme_content.strip()) >= readme_min_length else "warn",
            details=f"README length: {len(readme_content.strip())} characters.",
            recommendation=(
                None
                if len(readme_content.strip()) >= readme_min_length
                else "Expand README with setup, usage, and contribution notes."
            ),
        )
    )
    contributing_path = _find_first_path(tree_paths, lambda p: p.split("/")[-1] == "contributing.md")
    checks.append(
        CheckResult(
            id="contributing_exists",
            name="CONTRIBUTING file exists",
            status="pass" if contributing_path else "warn",
            details=f"Found at {contributing_path}" if contributing_path else "CONTRIBUTING.md not found.",
            recommendation=(
                None if contributing_path else "Add CONTRIBUTING.md describing contribution workflow."
            ),
        )
    )
    checks.append(
        CheckResult(
            id="license_exists",
            name="License metadata exists",
            status="pass" if snapshot.has_license else "warn",
            details="License detected." if snapshot.has_license else "No license metadata found via API.",
            recommendation=None if snapshot.has_license else "Add a LICENSE file and set repository license.",
        )
    )
    return checks


def ci_checks(snapshot: Any) -> list[CheckResult]:
    """Run CI/workflow quality checks."""

    workflows = snapshot.workflow_paths
    workflow_contents = [snapshot.file_contents.get(path, "") for path in workflows]

    checks: list[CheckResult] = []
    has_workflows = bool(workflows)
    checks.append(
        CheckResult(
            id="workflow_files",
            name="Workflow files exist",
            status="pass" if has_workflows else "fail",
            details=(
                f"Detected {len(workflows)} workflow files."
                if has_workflows
                else "No workflow files in .github/workflows."
            ),
            recommendation=None if has_workflows else "Add at least one GitHub Actions workflow.",
        )
    )

    trigger_status = "warn"
    trigger_details = "No workflow triggers found."
    trigger_rec = "Use on: [push, pull_request] in CI workflow."

    if has_workflows:
        found_trigger = False
        parse_errors = 0
        for content in workflow_contents:
            if not content.strip():
                continue
            try:
                for doc in yaml.safe_load_all(content):
                    if not isinstance(doc, dict):
                        continue
                    on_config = _extract_workflow_on_config(doc)
                    if _has_push_or_pr_trigger(on_config):
                        found_trigger = True
                        break
            except yaml.YAMLError:
                parse_errors += 1
            if found_trigger:
                break
        if found_trigger:
            trigger_status = "pass"
            trigger_details = "Found workflow trigger on push or pull_request."
            trigger_rec = None
        else:
            trigger_details = "No workflow configured for push or pull_request."
            if parse_errors:
                trigger_details += f" ({parse_errors} workflow files could not be parsed.)"

    checks.append(
        CheckResult(
            id="workflow_trigger",
            name="Workflow runs on push/pull_request",
            status=trigger_status,  # type: ignore[arg-type]
            details=trigger_details,
            recommendation=trigger_rec,
        )
    )

    stage_keywords = {
        "lint": ("lint", "ruff", "flake8", "eslint", "checkstyle", "stylecop", "clang-tidy"),
        "test": ("test", "pytest", "jest", "vitest", "dotnet test", "mvn test", "gradle test", "ctest"),
        "build": ("build", "compile", "package", "dotnet build", "mvn package", "cmake"),
        "release": ("release", "publish", "deploy", "upload-artifact", "gh release"),
    }
    combined = "\n".join(workflow_contents).lower()
    covered = 0
    for keywords in stage_keywords.values():
        if any(keyword in combined for keyword in keywords):
            covered += 1

    if not has_workflows:
        coverage_status = "fail"
        coverage_details = "CI stage coverage unavailable because workflows are missing."
    elif covered >= 3:
        coverage_status = "pass"
        coverage_details = f"Detected CI stage coverage for {covered}/4 stages."
    elif covered >= 1:
        coverage_status = "warn"
        coverage_details = f"Detected CI stage coverage for only {covered}/4 stages."
    else:
        coverage_status = "fail"
        coverage_details = "No recognizable lint/test/build/release stages in workflows."

    checks.append(
        CheckResult(
            id="ci_stage_coverage",
            name="CI covers key stages (lint/test/build/release)",
            status=coverage_status,  # type: ignore[arg-type]
            details=coverage_details,
            recommendation=(
                None
                if coverage_status == "pass"
                else "Expand workflows to cover lint, test, build and release stages."
            ),
        )
    )
    return checks


def quality_checks(snapshot: Any) -> list[CheckResult]:
    """Run test and lint configuration checks across ecosystems."""

    tree_paths_lower = [path.lower() for path in snapshot.tree_paths]
    pyproject_path = next((p for p in snapshot.tree_paths if p.lower().endswith("pyproject.toml")), None)
    pyproject_content = snapshot.file_contents.get(pyproject_path, "") if pyproject_path else ""
    package_json_path = next((p for p in snapshot.tree_paths if p.lower().endswith("package.json")), None)
    package_json_content = snapshot.file_contents.get(package_json_path, "") if package_json_path else ""
    java_build_paths = []
    for path in snapshot.tree_paths:
        if path.lower().endswith(("pom.xml", "build.gradle", "build.gradle.kts")):
            java_build_paths.append(path)
    java_build_content = "\n".join(snapshot.file_contents.get(path, "") for path in java_build_paths)

    lint_config_filenames = {
        ".pre-commit-config.yaml",
        ".flake8",
        "setup.cfg",
        "tox.ini",
        ".editorconfig",
        ".clang-format",
        ".clang-tidy",
        "checkstyle.xml",
        "stylecop.json",
    }
    lint_config_suffixes = (
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        ".prettierrc",
        ".prettierrc.js",
        ".prettierrc.cjs",
        ".prettierrc.json",
        ".ruleset",
    )

    has_py_lint = bool(pyproject_content) and (
        "[tool.ruff]" in pyproject_content or "[tool.black]" in pyproject_content
    )
    has_js_lint = any(
        path.endswith(("eslint.config.js", "eslint.config.cjs", "eslint.config.mjs"))
        or path.endswith(lint_config_suffixes)
        for path in tree_paths_lower
    ) or ("eslint" in package_json_content.lower() or "prettier" in package_json_content.lower())
    has_java_lint = "checkstyle" in java_build_content.lower() or "spotless" in java_build_content.lower()
    has_cpp_lint = any(path.endswith((".clang-format", ".clang-tidy")) for path in tree_paths_lower)
    has_cs_lint = any(
        path.endswith(("stylecop.json", ".ruleset", "directory.build.props")) for path in tree_paths_lower
    )
    has_generic_lint_file = any(path.split("/")[-1] in lint_config_filenames for path in tree_paths_lower)

    has_lint_config = any(
        [has_py_lint, has_js_lint, has_java_lint, has_cpp_lint, has_cs_lint, has_generic_lint_file]
    )

    test_dir_markers = ("tests/", "test/", "__tests__/", "spec/")
    has_tests_dir = any(marker in path for path in tree_paths_lower for marker in test_dir_markers)
    test_file_exts = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".cs",
        ".cpp",
        ".cc",
        ".cxx",
        ".go",
        ".rb",
    )
    has_test_files = any(
        ("test" in path.split("/")[-1] or path.split("/")[-1].endswith((".spec.js", ".spec.ts")))
        and path.endswith(test_file_exts)
        for path in tree_paths_lower
    )
    has_test_config = any(
        path.endswith(("jest.config.js", "jest.config.ts", "vitest.config.ts", "pytest.ini", "phpunit.xml"))
        for path in tree_paths_lower
    )
    has_tests = has_tests_dir or has_test_files or has_test_config

    return [
        CheckResult(
            id="lint_config",
            name="Linter/formatter config exists",
            status="pass" if has_lint_config else "warn",
            details=(
                "Found lint/format config."
                if has_lint_config
                else "No lint/format config found for common ecosystems."
            ),
            recommendation=(
                None
                if has_lint_config
                else "Add lint/format config (ruff/eslint/checkstyle/.clang-format/.editorconfig)."
            ),
        ),
        CheckResult(
            id="tests_exist",
            name="Tests exist",
            status="pass" if has_tests else "warn",
            details=(
                "Tests detected in repository."
                if has_tests
                else "No tests/ folder or test_*.py files found."
            ),
            recommendation=None if has_tests else "Add automated tests (tests/ or test_*.py).",
        ),
    ]


def security_checks(
    snapshot: Any,
    enable_network: bool = False,
    policy: RepoPolicy | None = None,
) -> list[CheckResult]:
    """Run action pinning and secret leakage checks."""

    policy = policy or RepoPolicy()
    workflow_contents = [snapshot.file_contents.get(path, "") for path in snapshot.workflow_paths]
    unpinned_actions: list[str] = []

    for content in workflow_contents:
        for _, ref in USES_RE.findall(content):
            if ref.startswith("${{"):
                unpinned_actions.append(ref)
                continue
            if not PINNED_SHA_RE.match(ref):
                unpinned_actions.append(ref)

    if not snapshot.workflow_paths:
        action_status = "warn"
        action_details = "No workflows found, pinning check skipped."
        action_recommendation = "Use pinned actions with full commit SHA when workflows are added."
    elif unpinned_actions:
        action_status = "warn"
        action_details = f"Found unpinned action refs: {', '.join(sorted(set(unpinned_actions)))}."
        action_recommendation = "Pin GitHub Actions to commit SHA (40 hex chars)."
    else:
        action_status = "pass"
        action_details = "All detected actions are pinned to commit SHA."
        action_recommendation = None

    secrets_found: list[str] = []
    for path, content in snapshot.file_contents.items():
        lower = path.lower()
        filename = lower.split("/")[-1]
        if not (
            filename.startswith("readme.")
            or lower.startswith(".github/workflows/")
            or lower.endswith("pyproject.toml")
            or lower.endswith(".env.example")
            or lower.endswith("package.json")
            or lower.endswith("pom.xml")
            or lower.endswith("build.gradle")
        ):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(content):
                token_value = match.group(0)
                if policy.is_secret_allowed(path, token_value):
                    continue
                secrets_found.append(f"{label} in {path}")

    if secrets_found:
        secret_status = "fail"
        secret_details = "Potential secrets found: " + "; ".join(sorted(set(secrets_found)))
        secret_rec = "Remove leaked secrets immediately and rotate affected credentials."
    else:
        secret_status = "pass"
        secret_details = "No predefined secret patterns detected in scanned files."
        secret_rec = None

    lockfile_names = {"requirements.txt", "poetry.lock", "package-lock.json", "pnpm-lock.yaml", "cargo.lock"}
    has_lockfile = any(path.lower().split("/")[-1] in lockfile_names for path in snapshot.tree_paths)
    has_dependabot = any(path.lower() == ".github/dependabot.yml" for path in snapshot.tree_paths)
    if has_lockfile and has_dependabot:
        dep_status = "pass"
        dep_details = "Dependency lockfile and dependabot config detected."
        dep_rec = None
    elif has_lockfile or has_dependabot:
        dep_status = "warn"
        dep_details = "Only partial dependency security setup detected."
        dep_rec = "Use lockfiles and configure .github/dependabot.yml."
    else:
        dep_status = "warn"
        dep_details = "No dependency lockfile or dependabot config detected."
        dep_rec = "Add lockfiles and enable dependency update automation."

    vulnerability_check = dependency_vulnerability_check(snapshot, enable_network=enable_network)
    return [
        CheckResult(
            id="actions_pinned",
            name="GitHub Actions are pinned",
            status=action_status,  # type: ignore[arg-type]
            details=action_details,
            recommendation=action_recommendation,
        ),
        CheckResult(
            id="secret_patterns",
            name="No exposed secret patterns",
            status=secret_status,  # type: ignore[arg-type]
            details=secret_details,
            recommendation=secret_rec,
        ),
        CheckResult(
            id="dependency_hygiene",
            name="Dependency security hygiene",
            status=dep_status,  # type: ignore[arg-type]
            details=dep_details,
            recommendation=dep_rec,
        ),
        vulnerability_check,
    ]


def dependency_vulnerability_check(snapshot: Any, enable_network: bool) -> CheckResult:
    """Query OSV for vulnerabilities in pinned dependencies."""

    dependency_refs = extract_dependency_refs(snapshot)
    if not dependency_refs:
        return CheckResult(
            id="dependency_vulnerabilities",
            name="Known vulnerabilities in dependencies",
            status="warn",
            details="No pinned dependencies detected for vulnerability scan.",
            recommendation="Use lockfiles and pinned versions to enable dependency vulnerability scanning.",
        )
    if not enable_network:
        return CheckResult(
            id="dependency_vulnerabilities",
            name="Known vulnerabilities in dependencies",
            status="warn",
            details="Vulnerability scan skipped (network disabled).",
            recommendation="Run scan with network access to query OSV database.",
        )

    try:
        findings = query_osv_for_dependencies(dependency_refs)
    except Exception as exc:
        return CheckResult(
            id="dependency_vulnerabilities",
            name="Known vulnerabilities in dependencies",
            status="warn",
            details=f"OSV query failed: {exc}",
            recommendation="Retry scan later; OSV API may be temporarily unavailable.",
        )

    if findings:
        sample = ", ".join(sorted({item["id"] for item in findings})[:5])
        return CheckResult(
            id="dependency_vulnerabilities",
            name="Known vulnerabilities in dependencies",
            status="fail",
            details=f"Found {len(findings)} vulnerability matches (e.g., {sample}).",
            recommendation="Upgrade affected dependencies and verify with security advisory references.",
        )
    return CheckResult(
        id="dependency_vulnerabilities",
        name="Known vulnerabilities in dependencies",
        status="pass",
        details=f"No OSV matches found across {len(dependency_refs)} dependencies.",
        recommendation=None,
    )


def extract_dependency_refs(snapshot: Any) -> list[DependencyRef]:
    """Extract dependencies from common lockfiles/manifests."""

    refs: set[DependencyRef] = set()
    for path, content in snapshot.file_contents.items():
        lower = path.lower()
        filename = lower.split("/")[-1]
        if filename in {"requirements.txt", "requirements-dev.txt"}:
            refs.update(_parse_requirements(content))
        elif filename == "poetry.lock":
            refs.update(_parse_poetry_lock(content))
        elif filename == "package-lock.json":
            refs.update(_parse_package_lock(content))
        elif filename == "package.json":
            refs.update(_parse_package_json(content))
        elif filename in {"pom.xml", "build.gradle", "build.gradle.kts"}:
            refs.update(_parse_maven_like(content))
        elif filename.endswith(".csproj"):
            refs.update(_parse_csproj(content))
        elif filename == "go.mod":
            refs.update(_parse_go_mod(content))
        elif filename == "cargo.lock":
            refs.update(_parse_cargo_lock(content))
        elif filename == "composer.lock":
            refs.update(_parse_composer_lock(content))
    ref_list = sorted(refs, key=lambda item: (item.ecosystem, item.name, item.version))
    return ref_list[:MAX_DEPENDENCIES_FOR_OSV]


def query_osv_for_dependencies(dependencies: list[DependencyRef]) -> list[dict[str, str]]:
    """Batch query OSV API for dependency vulnerabilities."""

    findings: list[dict[str, str]] = []
    with httpx.Client(timeout=httpx.Timeout(20.0)) as client:
        for chunk_start in range(0, len(dependencies), OSV_BATCH_SIZE):
            chunk = dependencies[chunk_start : chunk_start + OSV_BATCH_SIZE]
            queries = [
                {
                    "package": {"name": dep.name, "ecosystem": dep.ecosystem},
                    "version": dep.version,
                }
                for dep in chunk
            ]
            response = client.post(OSV_QUERY_URL, json={"queries": queries})
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            for dep, result in zip(chunk, results, strict=False):
                vulns = result.get("vulns", []) if isinstance(result, dict) else []
                for vuln in vulns:
                    vuln_id = vuln.get("id")
                    if not vuln_id:
                        continue
                    findings.append(
                        {
                            "id": str(vuln_id),
                            "package": f"{dep.ecosystem}:{dep.name}@{dep.version}",
                        }
                    )
    return findings


def maintenance_checks(snapshot: Any, stale_days: int = 180) -> list[CheckResult]:
    """Run release cadence and activity freshness checks."""

    checks: list[CheckResult] = []
    checks.append(
        CheckResult(
            id="releases_or_tags",
            name="Releases or tags exist",
            status="pass" if snapshot.has_release_or_tag else "warn",
            details=(
                "Release/tag metadata found."
                if snapshot.has_release_or_tag
                else "No releases or tags found."
            ),
            recommendation=(
                None if snapshot.has_release_or_tag else "Create semantic version tags and releases."
            ),
        )
    )

    last_activity = snapshot.pushed_at or snapshot.updated_at
    now = datetime.now(UTC)
    if last_activity is None:
        activity_status = "warn"
        details = "No activity timestamp available."
        recommendation = "Ensure repository metadata is available and updated."
    else:
        last = last_activity.astimezone(UTC)
        age_days = (now - last).days
        if age_days > stale_days:
            activity_status = "warn"
            details = f"Last activity was {age_days} days ago."
            recommendation = "Repository appears stale; plan maintenance or archive status."
        else:
            activity_status = "pass"
            details = f"Recent activity {age_days} days ago."
            recommendation = None

    checks.append(
        CheckResult(
            id="recent_activity",
            name=f"Recent activity (<={stale_days} days)",
            status=activity_status,  # type: ignore[arg-type]
            details=details,
            recommendation=recommendation,
        )
    )
    return checks


def governance_checks(snapshot: Any) -> list[CheckResult]:
    """Run repository governance checks (templates, CODEOWNERS, security policy)."""

    lower_paths = [path.lower() for path in snapshot.tree_paths]
    has_codeowners = any(path.endswith("codeowners") for path in lower_paths)
    has_pr_template = any(
        path.endswith(".github/pull_request_template.md")
        or path.startswith(".github/pull_request_template/")
        for path in lower_paths
    )
    has_issue_template = any(path.startswith(".github/issue_template/") for path in lower_paths)
    has_security_policy = any(path.endswith("security.md") for path in lower_paths)

    return [
        CheckResult(
            id="codeowners_exists",
            name="CODEOWNERS file exists",
            status="pass" if has_codeowners else "warn",
            details="CODEOWNERS found." if has_codeowners else "CODEOWNERS not found.",
            recommendation=None if has_codeowners else "Add CODEOWNERS for review ownership.",
        ),
        CheckResult(
            id="pr_template_exists",
            name="Pull request template exists",
            status="pass" if has_pr_template else "warn",
            details="PR template found." if has_pr_template else "PR template not found.",
            recommendation=None if has_pr_template else "Add .github/pull_request_template.md.",
        ),
        CheckResult(
            id="issue_template_exists",
            name="Issue template exists",
            status="pass" if has_issue_template else "warn",
            details="Issue template found." if has_issue_template else "Issue template not found.",
            recommendation=None if has_issue_template else "Add issue templates in .github/ISSUE_TEMPLATE/.",
        ),
        CheckResult(
            id="security_policy_exists",
            name="Security policy exists",
            status="pass" if has_security_policy else "warn",
            details="SECURITY.md found." if has_security_policy else "SECURITY.md not found.",
            recommendation=None if has_security_policy else "Add SECURITY.md with disclosure process.",
        ),
    ]


def run_all_checks(
    snapshot: Any,
    enable_network: bool = True,
    policy: RepoPolicy | None = None,
) -> dict[str, list[CheckResult]]:
    """Execute all check categories and apply policy-based filtering."""

    policy = policy or RepoPolicy()
    checks_by_category = {
        "docs": docs_checks(snapshot, readme_min_length=policy.readme_min_length),
        "ci": ci_checks(snapshot),
        "security": security_checks(snapshot, enable_network=enable_network, policy=policy),
        "quality": quality_checks(snapshot),
        "maintenance": maintenance_checks(snapshot, stale_days=policy.stale_days),
        "governance": governance_checks(snapshot),
    }
    checks_by_category["governance"].append(_policy_validity_check(policy))
    return apply_ignore_checks(checks_by_category, policy.ignore_checks)


def _policy_validity_check(policy: RepoPolicy) -> CheckResult:
    """Convert policy schema validity into explicit check result."""

    if policy.source_path is None:
        return CheckResult(
            id="policy_config_valid",
            name="Policy configuration file",
            status="pass",
            details="No policy file found. Using default settings.",
            recommendation=None,
        )
    if policy.is_valid:
        return CheckResult(
            id="policy_config_valid",
            name="Policy configuration file",
            status="pass",
            details=f"Policy loaded successfully from {policy.source_path}.",
            recommendation=None,
        )
    return CheckResult(
        id="policy_config_valid",
        name="Policy configuration file",
        status="warn",
        details=f"Policy has validation issues: {'; '.join(policy.validation_errors)}",
        recommendation="Fix .repo-inspector.yml schema issues to apply policy reliably.",
    )


def _has_push_or_pr_trigger(on_config: Any) -> bool:
    if isinstance(on_config, str):
        return on_config in {"push", "pull_request"}
    if isinstance(on_config, list):
        return any(item in {"push", "pull_request"} for item in on_config if isinstance(item, str))
    if isinstance(on_config, dict):
        return "push" in on_config or "pull_request" in on_config
    return False


def _extract_workflow_on_config(doc: dict[Any, Any]) -> Any:
    """Extract workflow trigger config from parsed YAML document.

    Notes:
    - PyYAML may parse the key `on` as boolean `True` (YAML 1.1 behavior).
    - GitHub Actions treats `on` as a literal key (YAML 1.2 behavior).
    """

    if "on" in doc:
        return doc.get("on")
    if True in doc:
        return doc.get(True)
    for key, value in doc.items():
        if isinstance(key, str) and key.lower() == "on":
            return value
    return None


def _parse_requirements(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    for raw_line in content.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.match(r"^([A-Za-z0-9_.\-]+)==([A-Za-z0-9_.+\-!]+)$", line)
        if not match:
            continue
        refs.add(DependencyRef(ecosystem="PyPI", name=match.group(1), version=match.group(2)))
    return refs


def _parse_poetry_lock(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    pattern = re.compile(r'name = "([^"]+)"\s+version = "([^"]+)"', re.MULTILINE)
    for name, version in pattern.findall(content):
        refs.add(DependencyRef(ecosystem="PyPI", name=name, version=version))
    return refs


def _parse_package_json(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    payload = _safe_json_load(content)
    if not isinstance(payload, dict):
        return refs
    for section in ("dependencies", "devDependencies"):
        deps = payload.get(section, {})
        if not isinstance(deps, dict):
            continue
        for name, raw_version in deps.items():
            if not isinstance(raw_version, str):
                continue
            version = raw_version.strip().lstrip("^~")
            if re.match(r"^\d+(\.\d+){0,3}([\-+][A-Za-z0-9.\-]+)?$", version):
                refs.add(DependencyRef(ecosystem="npm", name=name, version=version))
    return refs


def _parse_package_lock(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    payload = _safe_json_load(content)
    if not isinstance(payload, dict):
        return refs

    dependencies = payload.get("dependencies", {})
    if isinstance(dependencies, dict):
        for name, info in dependencies.items():
            if not isinstance(info, dict):
                continue
            version = info.get("version")
            if isinstance(version, str):
                refs.add(DependencyRef(ecosystem="npm", name=name, version=version))

    packages = payload.get("packages", {})
    if isinstance(packages, dict):
        for package_path, info in packages.items():
            if not isinstance(info, dict):
                continue
            version = info.get("version")
            if not isinstance(version, str):
                continue
            if package_path.startswith("node_modules/"):
                name = package_path.split("node_modules/")[-1]
                refs.add(DependencyRef(ecosystem="npm", name=name, version=version))
    return refs


def _parse_maven_like(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    pattern = re.compile(
        r"<dependency>.*?<groupId>([^<]+)</groupId>.*?<artifactId>([^<]+)</artifactId>.*?<version>([^<]+)</version>.*?</dependency>",
        re.DOTALL,
    )
    for group_id, artifact_id, version in pattern.findall(content):
        refs.add(DependencyRef(ecosystem="Maven", name=f"{group_id}:{artifact_id}", version=version.strip()))
    return refs


def _parse_csproj(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    pattern = re.compile(
        r"<PackageReference[^>]*Include=\"([^\"]+)\"[^>]*Version=\"([^\"]+)\"",
        re.IGNORECASE,
    )
    for name, version in pattern.findall(content):
        refs.add(DependencyRef(ecosystem="NuGet", name=name.strip(), version=version.strip()))
    return refs


def _parse_go_mod(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    for line in content.splitlines():
        match = re.match(r"^\s*([A-Za-z0-9./\-_]+)\s+v([0-9A-Za-z.\-+]+)\s*$", line)
        if match:
            refs.add(DependencyRef(ecosystem="Go", name=match.group(1), version=f"v{match.group(2)}"))
    return refs


def _parse_cargo_lock(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    pattern = re.compile(r'name = "([^"]+)"\s+version = "([^"]+)"', re.MULTILINE)
    for name, version in pattern.findall(content):
        refs.add(DependencyRef(ecosystem="crates.io", name=name, version=version))
    return refs


def _parse_composer_lock(content: str) -> set[DependencyRef]:
    refs: set[DependencyRef] = set()
    payload = _safe_json_load(content)
    if not isinstance(payload, dict):
        return refs
    for section in ("packages", "packages-dev"):
        packages = payload.get(section, [])
        if not isinstance(packages, list):
            continue
        for package in packages:
            if not isinstance(package, dict):
                continue
            name = package.get("name")
            version = package.get("version")
            if isinstance(name, str) and isinstance(version, str):
                refs.add(DependencyRef(ecosystem="Packagist", name=name, version=version))
    return refs


def _safe_json_load(content: str) -> Any:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def _count_lines(content: str) -> int:
    if not content:
        return 0
    line_count = content.count("\n")
    if not content.endswith("\n"):
        line_count += 1
    return line_count


def _extension(path: str) -> str:
    lower = path.lower()
    idx = lower.rfind(".")
    return lower[idx:] if idx >= 0 else "no_ext"
