from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.scanner.checks import (
    ci_checks,
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


def test_ci_trigger_warn_without_push_or_pr():
    snap = snapshot_factory(
        file_contents={".github/workflows/ci.yml": "name: ci\non: workflow_dispatch\njobs: {}"},
        tree_paths=[".github/workflows/ci.yml"],
    )
    checks = ci_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["workflow_files"] == "pass"
    assert statuses["workflow_trigger"] == "warn"


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


def test_detect_stacks_python_js():
    snap = snapshot_factory(tree_paths=["pyproject.toml", "package.json", "src/main.py"], file_contents={})
    stacks = detect_stacks(snap)
    assert "python" in stacks
    assert "javascript" in stacks


def test_governance_warn_when_missing_files():
    snap = snapshot_factory(tree_paths=["README.md"], file_contents={"README.md": "A" * 250})
    checks = governance_checks(snap)
    statuses = {c.id: c.status for c in checks}
    assert statuses["codeowners_exists"] == "warn"
    assert statuses["security_policy_exists"] == "warn"


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
