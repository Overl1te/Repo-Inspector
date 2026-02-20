"""Scoring engine for per-category and total repository quality score."""

from datetime import UTC, datetime

from app.scanner.schemas import (
    CategoryReport,
    CheckResult,
    FixPlanItem,
    ProjectMetrics,
    ReportComparison,
    ReportSummary,
)

CATEGORY_WEIGHTS = {
    "docs": ("Docs", 15),
    "ci": ("CI", 15),
    "security": ("Security", 25),
    "quality": ("Quality", 20),
    "maintenance": ("Maintenance", 15),
    "governance": ("Governance", 10),
}

STATUS_FACTOR = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
TARGET_TOTAL_WEIGHT = 100
NON_SCORING_CHECK_IDS = {"policy_config_valid", "score_regression_guard"}
CHECK_IMPORTANCE = {
    "docs": {
        "readme_exists": 1.7,
        "readme_length": 1.0,
        "contributing_exists": 0.9,
        "license_exists": 1.2,
        "changelog_exists": 0.8,
        "docs_dir_exists": 0.7,
        "readme_usage_section": 0.9,
    },
    "ci": {
        "workflow_files": 1.7,
        "workflow_trigger": 1.3,
        "ci_stage_coverage": 1.2,
        "workflow_yaml_valid": 0.9,
        "ci_cache_configured": 0.8,
        "workflow_timeouts": 0.8,
    },
    "security": {
        "actions_pinned": 1.3,
        "secret_patterns": 2.4,
        "dependency_hygiene": 1.1,
        "workflow_permissions": 1.2,
        "security_contact": 0.9,
        "dependency_vulnerabilities": 2.1,
    },
    "quality": {
        "lint_config": 1.1,
        "editorconfig_exists": 0.8,
        "tests_exist": 1.7,
        "tests_run_in_ci": 1.0,
    },
    "maintenance": {
        "releases_or_tags": 1.2,
        "recent_activity": 1.4,
        "support_docs": 0.7,
        "release_notes_file": 0.8,
    },
    "governance": {
        "codeowners_exists": 1.2,
        "pr_template_exists": 1.0,
        "issue_template_exists": 1.0,
        "security_policy_exists": 1.5,
        "code_of_conduct_exists": 1.1,
        "funding_config_exists": 0.6,
        "score_regression_guard": 2.0,
        "policy_config_valid": 0.8,
    },
}


def build_report(
    repo_owner: str,
    repo_name: str,
    repo_url: str,
    checks_by_category: dict[str, list[CheckResult]],
    project_metrics: ProjectMetrics,
    detected_stacks: list[str] | None = None,
    category_weights: dict[str, int] | None = None,
    job_id: str | None = None,
    commit_sha: str | None = None,
    comparison: ReportComparison | None = None,
    policy_issues: list[str] | None = None,
) -> ReportSummary:
    """Build normalized report object from categorized checks."""

    resolved_weights = _resolve_weights(category_weights or {})
    categories: list[CategoryReport] = []
    total_score = 0.0

    for category_id, (category_name, weight) in resolved_weights.items():
        checks = checks_by_category.get(category_id, [])
        category_score = _score_category(category_id, weight, checks)
        total_score += category_score
        recommendations = sorted(
            {
                check.recommendation
                for check in checks
                if check.recommendation and check.status in {"warn", "fail"}
            }
        )
        categories.append(
            CategoryReport(
                id=category_id,
                name=category_name,
                weight=weight,
                score=round(category_score),
                checks=checks,
                recommendations=recommendations,
            )
        )

    fix_plan = build_fix_plan(categories)
    return ReportSummary(
        job_id=job_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        repo_url=repo_url,
        generated_at=datetime.now(UTC).isoformat(),
        score_total=round(total_score),
        commit_sha=commit_sha,
        detected_stacks=detected_stacks or [],
        project_metrics=project_metrics,
        categories=categories,
        fix_plan=fix_plan,
        comparison=comparison,
        policy_issues=policy_issues or [],
    )


def build_fix_plan(categories: list[CategoryReport]) -> list[FixPlanItem]:
    """Create prioritized remediation plan from non-passing checks."""

    items: list[FixPlanItem] = []
    for category in categories:
        check_weights = _check_weight_map(category.id, category.weight, category.checks)
        for check in category.checks:
            factor = STATUS_FACTOR[check.status]
            if check.status == "pass":
                continue
            check_weight = check_weights.get(check.id, 0.0)
            impact = round(check_weight * (1.0 - factor), 2)
            action = check.recommendation or "Review this check and apply the suggested best practice."
            items.append(
                FixPlanItem(
                    priority=0,
                    category_id=category.id,
                    category_name=category.name,
                    check_id=check.id,
                    check_name=check.name,
                    status=check.status,
                    impact_points=impact,
                    action=action,
                )
            )
    items.sort(key=lambda item: (0 if item.status == "fail" else 1, -item.impact_points, item.category_name))
    for idx, item in enumerate(items, start=1):
        item.priority = idx
    return items


def _resolve_weights(overrides: dict[str, int]) -> dict[str, tuple[str, int]]:
    """Merge category weight overrides into defaults."""

    resolved = dict(CATEGORY_WEIGHTS)
    for key, value in overrides.items():
        if key in resolved and value > 0:
            resolved[key] = (resolved[key][0], int(value))
    return _normalize_category_weights(resolved)


def _score_category(category_id: str, weight: int, checks: list[CheckResult]) -> float:
    """Calculate category score with per-check importance."""

    if not checks:
        return 0.0
    check_weights = _check_weight_map(category_id, weight, checks)
    score = 0.0
    for check in checks:
        score += check_weights.get(check.id, 0.0) * STATUS_FACTOR[check.status]
    return score


def _check_weight_map(category_id: str, category_weight: int, checks: list[CheckResult]) -> dict[str, float]:
    """Distribute category weight across checks using importance factors."""

    check_ids = [check.id for check in checks]
    return check_weight_map(category_id, category_weight, check_ids)


def check_weight_map(category_id: str, category_weight: int, check_ids: list[str]) -> dict[str, float]:
    """Distribute category weight across check identifiers using importance factors."""

    if not check_ids or category_weight <= 0:
        return {}
    weighted_checks: list[tuple[str, float]] = []
    total_importance = 0.0
    for check_id in check_ids:
        if check_id in NON_SCORING_CHECK_IDS:
            continue
        importance = _check_importance(category_id, check_id)
        weighted_checks.append((check_id, importance))
        total_importance += importance
    if total_importance <= 0:
        return {}

    by_check_id: dict[str, float] = {}
    for check_id, importance in weighted_checks:
        by_check_id[check_id] = by_check_id.get(check_id, 0.0) + (
            category_weight * (importance / total_importance)
        )
    return by_check_id


def _check_importance(category_id: str, check_id: str) -> float:
    """Return stable per-check importance factor."""

    category = CHECK_IMPORTANCE.get(category_id, {})
    value = float(category.get(check_id, 1.0))
    return value if value > 0 else 1.0


def _normalize_category_weights(
    raw_weights: dict[str, tuple[str, int]],
) -> dict[str, tuple[str, int]]:
    """Normalize category weights so total score remains in 0..100."""

    total = sum(weight for _, weight in raw_weights.values())
    if total <= 0:
        return dict(CATEGORY_WEIGHTS)
    if total == TARGET_TOTAL_WEIGHT:
        return raw_weights

    rows: list[tuple[str, str, int, float, int]] = []
    floor_total = 0
    for category_id, (name, weight) in raw_weights.items():
        exact = (weight / total) * TARGET_TOTAL_WEIGHT
        floor_val = int(exact)
        floor_total += floor_val
        rows.append((category_id, name, floor_val, exact - floor_val, weight))

    budget = TARGET_TOTAL_WEIGHT - floor_total
    rows.sort(key=lambda item: (-item[3], -item[4], item[0]))

    distributed: dict[str, tuple[str, int]] = {}
    for index, (category_id, name, floor_val, _, _) in enumerate(rows):
        extra = 1 if index < budget else 0
        distributed[category_id] = (name, floor_val + extra)

    ordered: dict[str, tuple[str, int]] = {}
    for category_id in CATEGORY_WEIGHTS:
        if category_id in distributed:
            ordered[category_id] = distributed[category_id]
    return ordered
