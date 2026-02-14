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
        category_score = _score_category(weight, checks)
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
        checks_count = len(category.checks) if category.checks else 1
        check_weight = category.weight / checks_count
        for check in category.checks:
            factor = STATUS_FACTOR[check.status]
            if check.status == "pass":
                continue
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


def _score_category(weight: int, checks: list[CheckResult]) -> float:
    """Calculate weighted category score using status factors."""

    if not checks:
        return 0.0
    part = weight / len(checks)
    score = 0.0
    for check in checks:
        score += part * STATUS_FACTOR[check.status]
    return score


def _resolve_weights(overrides: dict[str, int]) -> dict[str, tuple[str, int]]:
    """Merge category weight overrides into defaults."""

    resolved = dict(CATEGORY_WEIGHTS)
    for key, value in overrides.items():
        if key in resolved and value > 0:
            resolved[key] = (resolved[key][0], int(value))
    return resolved
