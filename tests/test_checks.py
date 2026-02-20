from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.scanner.checks import (
    ci_checks,
    dependency_vulnerability_check,
    detect_stacks,
    docs_checks,
    extract_dependency_refs,
    governance_checks,
    maintenance_checks,
    project_line_metrics,
    quality_checks,
    security_checks,
)
from app.scanner.i18n import localize_report
from app.scanner.policy import load_repo_policy


def snapshot_factory(**overrides):
    now = datetime.now(UTC)
    base = {
        "tree_paths": [
            "README.md",
            "CONTRIBUTING.md",
            "pyproject.toml",
            ".github/workflows/ci.yml",
            "tests/test_sample.py",
        ],
        "file_contents": {
            "README.md": "A" * 250,
            "CONTRIBUTING.md": "Please open a PR.",
            "pyproject.toml": "[tool.ruff]\nline-length = 100",
            ".github/workflows/ci.yml": "name: ci\non: [push, pull_request]\njobs: {}",
            "tests/test_sample.py": "def test_ok():\n    assert True\n",
        },
        "has_license": True,
        "workflow_paths": [".github/workflows/ci.yml"],
        "has_release_or_tag": True,
        "pushed_at": now - timedelta(days=5),
        "updated_at": now - timedelta(days=5),
        "line_count_paths": [],
        "line_count_candidates_total": 0,
        "line_count_sampled": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_docs_readme_length_pass():
    checks = docs_checks(snapshot_factory())
    statuses = {c.id: c.status for c in checks}
    assert statuses["readme_exists"] == "pass"
    assert statuses["readme_length"] == "pass"


def test_docs_contributing_warn_when_missing():
    snap = snapshot_factory(
        tree_paths=["README.md"],
        file_contents={"README.md": "A" * 220},
        has_license=True,
    )
    checks = docs_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["contributing_exists"] == "warn"


def test_docs_additional_checks_detect_changelog_docs_and_usage():
    snap = snapshot_factory(
        tree_paths=["README.md", "docs/architecture.md", "CHANGELOG.md"],
        file_contents={"README.md": "## Getting started\nInstall and usage instructions.\n"},
    )
    checks = docs_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["changelog_exists"] == "pass"
    assert statuses["docs_dir_exists"] == "pass"
    assert statuses["readme_usage_section"] == "pass"


def test_ci_trigger_warn_without_push_or_pr():
    snap = snapshot_factory(
        file_contents={".github/workflows/ci.yml": "name: ci\non: workflow_dispatch\njobs: {}"},
        tree_paths=[".github/workflows/ci.yml"],
    )
    checks = ci_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["workflow_files"] == "pass"
    assert statuses["workflow_trigger"] == "warn"


def test_ci_additional_checks_detect_yaml_cache_and_timeout():
    workflow = (
        "name: ci\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    timeout-minutes: 15\n"
        "    steps:\n"
        "      - uses: actions/cache@v4\n"
    )
    snap = snapshot_factory(
        tree_paths=[".github/workflows/ci.yml"],
        file_contents={".github/workflows/ci.yml": workflow},
    )
    checks = ci_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["workflow_yaml_valid"] == "pass"
    assert statuses["ci_cache_configured"] == "pass"
    assert statuses["workflow_timeouts"] == "pass"


def test_ci_trigger_pass_with_on_key_parsed_as_yaml_bool():
    snap = snapshot_factory(
        file_contents={
            ".github/workflows/ci.yml": (
                "name: ci\n"
                "on:\n"
                "  push:\n"
                "  pull_request:\n"
                "jobs: {}\n"
            )
        },
        tree_paths=[".github/workflows/ci.yml"],
    )
    checks = ci_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["workflow_files"] == "pass"
    assert statuses["workflow_trigger"] == "pass"


def test_security_secret_pattern_fail():
    snap = snapshot_factory(file_contents={"README.md": "Token: ghp_abcdefghijklmnopqrstuvwxyz12345"})
    checks = security_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["secret_patterns"] == "fail"


def test_security_additional_checks_permissions_and_contact():
    snap = snapshot_factory(
        tree_paths=[".github/workflows/ci.yml", "SECURITY.md"],
        file_contents={
            ".github/workflows/ci.yml": (
                "name: ci\n"
                "on: [push]\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs: {}\n"
            ),
            "SECURITY.md": "Report vulnerabilities to security@example.com",
        },
    )
    checks = security_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["workflow_permissions"] == "pass"
    assert statuses["security_contact"] == "pass"


def test_dependency_vulnerability_check_is_neutral_when_network_disabled():
    snap = snapshot_factory(
        tree_paths=["requirements.txt"],
        file_contents={"requirements.txt": "fastapi==0.111.0\n"},
    )
    check = dependency_vulnerability_check(snap, enable_network=False)
    assert check.status == "pass"
    assert check.recommendation is None


def test_quality_checks_warn_without_tests():
    snap = snapshot_factory(
        tree_paths=["pyproject.toml"],
        file_contents={"pyproject.toml": "[tool.black]\nline-length = 88"},
    )
    checks = quality_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["lint_config"] == "pass"
    assert statuses["tests_exist"] == "warn"


def test_maintenance_recent_activity_warn_if_stale():
    stale = datetime.now(UTC) - timedelta(days=240)
    snap = snapshot_factory(pushed_at=stale, updated_at=stale)
    checks = maintenance_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["recent_activity"] == "warn"


def test_quality_checks_detect_js_lint_config():
    snap = snapshot_factory(
        tree_paths=["package.json", "src/index.ts", "tests/app.test.ts"],
        file_contents={"package.json": '{"devDependencies":{"eslint":"^9.0.0"}}'},
    )
    checks = quality_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["lint_config"] == "pass"
    assert statuses["tests_exist"] == "pass"


def test_quality_checks_detect_editorconfig_and_ci_test_step():
    workflow = (
        "name: ci\n"
        "on: [push]\n"
        "jobs:\n"
        "  test:\n"
        "    steps:\n"
        "      - run: pytest\n"
    )
    snap = snapshot_factory(
        tree_paths=["pyproject.toml", ".editorconfig", ".github/workflows/ci.yml"],
        file_contents={
            "pyproject.toml": "[tool.ruff]\nline-length = 100",
            ".github/workflows/ci.yml": workflow,
        },
    )
    checks = quality_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["editorconfig_exists"] == "pass"
    assert statuses["tests_run_in_ci"] == "pass"


def test_localize_report_ru_changes_check_name():
    payload = {
        "repo_url": "https://github.com/a/b",
        "generated_at": "2026-01-01T00:00:00Z",
        "score_total": 80,
        "categories": [
            {
                "id": "docs",
                "name": "Docs",
                "weight": 20,
                "score": 10,
                "checks": [
                    {
                        "id": "readme_exists",
                        "name": "README file exists",
                        "status": "pass",
                        "details": "Found at README.md",
                        "recommendation": None,
                    }
                ],
                "recommendations": [],
            }
        ],
    }
    localized = localize_report(payload, "ru")
    assert localized["categories"][0]["name"] == "Документация"
    assert localized["categories"][0]["checks"][0]["name"] == "Наличие README"


def test_localize_report_ru_translates_new_check_and_fix_plan_action():
    expected_name = "\u041d\u0430\u043b\u0438\u0447\u0438\u0435 .editorconfig"
    expected_action = (
        "\u0414\u043e\u0431\u0430\u0432\u044c\u0442\u0435 .editorconfig "
        "\u0434\u043b\u044f \u0435\u0434\u0438\u043d\u044b\u0445 "
        "\u043d\u0430\u0441\u0442\u0440\u043e\u0435\u043a "
        "\u0440\u0435\u0434\u0430\u043a\u0442\u043e\u0440\u0430."
    )
    payload = {
        "repo_url": "https://github.com/a/b",
        "generated_at": "2026-01-01T00:00:00Z",
        "score_total": 70,
        "categories": [
            {
                "id": "quality",
                "name": "Quality",
                "weight": 20,
                "score": 10,
                "checks": [
                    {
                        "id": "editorconfig_exists",
                        "name": ".editorconfig exists",
                        "status": "warn",
                        "details": ".editorconfig not found.",
                        "recommendation": "Add .editorconfig for consistent editor settings.",
                    }
                ],
                "recommendations": ["Add .editorconfig for consistent editor settings."],
            }
        ],
        "fix_plan": [
            {
                "priority": 1,
                "category_id": "quality",
                "category_name": "Quality",
                "check_id": "editorconfig_exists",
                "check_name": ".editorconfig exists",
                "status": "warn",
                "impact_points": 1.0,
                "action": "Add .editorconfig for consistent editor settings.",
            }
        ],
    }
    localized = localize_report(payload, "ru")
    assert localized["categories"][0]["checks"][0]["name"] == expected_name
    assert localized["categories"][0]["checks"][0]["recommendation"] == expected_action
    assert localized["fix_plan"][0]["check_name"] == expected_name
    assert localized["fix_plan"][0]["action"] == expected_action


def test_detect_stacks_python_js():
    snap = snapshot_factory(tree_paths=["pyproject.toml", "package.json", "src/main.py"], file_contents={})
    stacks = detect_stacks(snap)
    assert "python" in stacks
    assert "javascript" in stacks


def test_detect_stacks_dart():
    snap = snapshot_factory(tree_paths=["pubspec.yaml", "lib/main.dart"], file_contents={})
    stacks = detect_stacks(snap)
    assert "dart" in stacks


def test_detect_stacks_typescript_terraform_shell_and_docker():
    snap = snapshot_factory(
        tree_paths=[
            "package.json",
            "tsconfig.json",
            "src/index.ts",
            "infra/main.tf",
            "scripts/deploy.sh",
            "Dockerfile",
        ],
        file_contents={},
    )
    stacks = detect_stacks(snap)
    assert "typescript" in stacks
    assert "javascript" in stacks
    assert "terraform" in stacks
    assert "shell" in stacks
    assert "docker" in stacks


def test_detect_stacks_html_and_css():
    snap = snapshot_factory(
        tree_paths=[
            "web/index.html",
            "web/style.css",
            "web/theme.scss",
        ],
        file_contents={},
    )
    stacks = detect_stacks(snap)
    assert "html" in stacks
    assert "css" in stacks


def test_governance_warn_when_missing_files():
    snap = snapshot_factory(tree_paths=["README.md"], file_contents={"README.md": "A" * 250})
    checks = governance_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["codeowners_exists"] == "warn"
    assert statuses["security_policy_exists"] == "warn"
    assert statuses["code_of_conduct_exists"] == "warn"


def test_maintenance_additional_checks_support_and_release_notes():
    snap = snapshot_factory(tree_paths=["SUPPORT.md", "CHANGELOG.md"], file_contents={})
    checks = maintenance_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["support_docs"] == "pass"
    assert statuses["release_notes_file"] == "pass"


def test_governance_additional_checks_pass_when_present():
    snap = snapshot_factory(
        tree_paths=[".github/CODEOWNERS", "CODE_OF_CONDUCT.md", ".github/FUNDING.yml", "SECURITY.md"],
        file_contents={},
    )
    checks = governance_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["code_of_conduct_exists"] == "pass"
    assert statuses["funding_config_exists"] == "pass"


def test_extract_dependency_refs_from_requirements_and_package_json():
    snap = snapshot_factory(
        tree_paths=["requirements.txt", "package.json"],
        file_contents={
            "requirements.txt": "fastapi==0.120.0\nuvicorn==0.32.0",
            "package.json": '{"dependencies":{"react":"18.3.1"}}',
        },
    )
    refs = extract_dependency_refs(snap)
    triples = {(item.ecosystem, item.name, item.version) for item in refs}
    assert ("PyPI", "fastapi", "0.120.0") in triples
    assert ("npm", "react", "18.3.1") in triples


def test_extract_dependency_refs_from_pubspec_files():
    snap = snapshot_factory(
        tree_paths=["pubspec.yaml", "pubspec.lock"],
        file_contents={
            "pubspec.yaml": (
                "dependencies:\n"
                "  dio: ^5.4.0\n"
                "dev_dependencies:\n"
                "  flutter_lints: ^5.0.0\n"
            ),
            "pubspec.lock": (
                "packages:\n"
                "  dio:\n"
                "    dependency: direct main\n"
                "    version: \"5.4.3+1\"\n"
            ),
        },
    )
    refs = extract_dependency_refs(snap)
    triples = {(item.ecosystem, item.name, item.version) for item in refs}
    assert ("Pub", "dio", "5.4.3+1") in triples
    assert ("Pub", "flutter_lints", "5.0.0") in triples


def test_project_line_metrics_counts_lines():
    snap = snapshot_factory(
        line_count_paths=["a.py", "src/main.js"],
        line_count_candidates_total=2,
        line_count_sampled=False,
        file_contents={"a.py": "print(1)\nprint(2)\n", "src/main.js": "const x = 1;\n"},
    )
    metrics = project_line_metrics(snap)
    assert metrics.total_code_files == 2
    assert metrics.total_code_lines == 3


def test_project_line_metrics_uses_extensionless_file_labels():
    snap = snapshot_factory(
        line_count_paths=["Dockerfile", "Makefile"],
        line_count_candidates_total=2,
        line_count_sampled=False,
        file_contents={"Dockerfile": "FROM python:3.12\n", "Makefile": "build:\n\t@echo ok\n"},
    )
    metrics = project_line_metrics(snap)
    labels = {item.extension for item in metrics.by_extension}
    assert "dockerfile" in labels
    assert "makefile" in labels
    assert "no_ext" not in labels


def test_quality_checks_detect_dart_lint_and_tests():
    snap = snapshot_factory(
        tree_paths=[
            "pubspec.yaml",
            "analysis_options.yaml",
            "test/widget_test.dart",
        ],
        file_contents={
            "pubspec.yaml": (
                "dev_dependencies:\n"
                "  flutter_test:\n"
                "    sdk: flutter\n"
                "  flutter_lints: ^5.0.0\n"
            )
        },
    )
    checks = quality_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["lint_config"] == "pass"
    assert statuses["tests_exist"] == "pass"


def test_secret_allowlist_ignores_known_prefix_in_readme():
    snap = snapshot_factory(
        tree_paths=["README.md", ".repo-inspector.yml"],
        file_contents={
            "README.md": "Example key: AKIAAAAAAAAAAAAAAAAA",
            ".repo-inspector.yml": (
                "security:\n"
                "  secret_allowlist_patterns:\n"
                "    - AKIA\n"
            ),
        },
    )
    policy = load_repo_policy(snap)
    checks = security_checks(snap, policy=policy)
    statuses = {c.id: c.status for c in checks}
    assert statuses["secret_patterns"] == "pass"


def test_invalid_policy_marks_validation_errors():
    snap = snapshot_factory(
        tree_paths=[".repo-inspector.yml"],
        file_contents={".repo-inspector.yml": "scoring:\n  category_weights: []\n"},
    )
    policy = load_repo_policy(snap)
    assert policy.validation_errors
