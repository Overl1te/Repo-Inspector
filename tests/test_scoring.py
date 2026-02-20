from app.scanner.schemas import CheckResult, ProjectMetrics
from app.scanner.scoring import build_report, check_weight_map


def _metrics() -> ProjectMetrics:
    return ProjectMetrics(
        total_code_files=10,
        total_code_lines=1000,
        scanned_code_files=10,
        sampled=False,
        by_extension=[],
    )


def _check(check_id: str, status: str) -> CheckResult:
    return CheckResult(
        id=check_id,
        name=check_id,
        status=status,  # type: ignore[arg-type]
        details=check_id,
        recommendation=None,
    )


def _base_checks() -> dict[str, list[CheckResult]]:
    return {
        "docs": [_check("readme_exists", "pass")],
        "ci": [_check("workflow_files", "pass")],
        "security": [_check("actions_pinned", "pass")],
        "quality": [_check("tests_exist", "pass")],
        "maintenance": [_check("recent_activity", "pass")],
        "governance": [_check("security_policy_exists", "pass")],
    }


def _category_score(report, category_id: str) -> int:
    return next(item.score for item in report.categories if item.id == category_id)


def test_security_critical_fail_penalizes_more_than_minor_fail():
    critical = _base_checks()
    critical["security"] = [
        _check("secret_patterns", "fail"),
        _check("dependency_hygiene", "pass"),
    ]
    minor = _base_checks()
    minor["security"] = [
        _check("secret_patterns", "pass"),
        _check("dependency_hygiene", "fail"),
    ]

    report_critical = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=critical,
        project_metrics=_metrics(),
    )
    report_minor = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=minor,
        project_metrics=_metrics(),
    )

    assert _category_score(report_critical, "security") < _category_score(report_minor, "security")
    assert report_critical.score_total < report_minor.score_total


def test_category_weights_are_normalized_to_100():
    report = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=_base_checks(),
        project_metrics=_metrics(),
        category_weights={
            "docs": 50,
            "ci": 50,
            "security": 50,
            "quality": 50,
            "maintenance": 50,
            "governance": 50,
        },
    )
    assert sum(item.weight for item in report.categories) == 100
    assert report.score_total == 100


def test_fix_plan_uses_importance_for_priority():
    checks = _base_checks()
    checks["security"] = [
        _check("secret_patterns", "fail"),
        _check("dependency_hygiene", "fail"),
    ]

    report = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=checks,
        project_metrics=_metrics(),
    )
    by_id = {item.check_id: item for item in report.fix_plan}
    assert by_id["secret_patterns"].impact_points > by_id["dependency_hygiene"].impact_points


def test_policy_check_does_not_inflate_score():
    checks_without_policy = _base_checks()
    checks_without_policy["governance"] = [_check("codeowners_exists", "fail")]

    checks_with_policy = _base_checks()
    checks_with_policy["governance"] = [
        _check("codeowners_exists", "fail"),
        _check("policy_config_valid", "pass"),
    ]

    report_without_policy = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=checks_without_policy,
        project_metrics=_metrics(),
    )
    report_with_policy = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=checks_with_policy,
        project_metrics=_metrics(),
    )

    assert _category_score(report_with_policy, "governance") == _category_score(
        report_without_policy,
        "governance",
    )
    assert report_with_policy.score_total == report_without_policy.score_total


def test_score_regression_guard_is_non_scoring():
    checks_without_guard = _base_checks()
    checks_without_guard["governance"] = [_check("codeowners_exists", "fail")]

    checks_with_guard = _base_checks()
    checks_with_guard["governance"] = [
        _check("codeowners_exists", "fail"),
        _check("score_regression_guard", "fail"),
    ]

    report_without_guard = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=checks_without_guard,
        project_metrics=_metrics(),
    )
    report_with_guard = build_report(
        repo_owner="octocat",
        repo_name="repo",
        repo_url="https://github.com/octocat/repo",
        checks_by_category=checks_with_guard,
        project_metrics=_metrics(),
    )

    assert _category_score(report_with_guard, "governance") == _category_score(
        report_without_guard,
        "governance",
    )
    assert report_with_guard.score_total == report_without_guard.score_total


def test_check_weight_map_skips_non_scoring_checks():
    weights = check_weight_map(
        "governance",
        10,
        ["codeowners_exists", "policy_config_valid", "score_regression_guard"],
    )
    assert "policy_config_valid" not in weights
    assert "score_regression_guard" not in weights
    assert round(weights.get("codeowners_exists", 0.0), 4) == 10.0
