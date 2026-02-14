from typing import Literal

from pydantic import BaseModel, Field

CheckStatus = Literal["pass", "warn", "fail"]


class CheckResult(BaseModel):
    id: str
    name: str
    status: CheckStatus
    details: str
    recommendation: str | None = None


class CategoryReport(BaseModel):
    id: str
    name: str
    weight: int
    score: int
    checks: list[CheckResult] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class ExtensionMetric(BaseModel):
    extension: str
    files: int
    lines: int


class ProjectMetrics(BaseModel):
    total_code_files: int
    total_code_lines: int
    scanned_code_files: int
    sampled: bool = False
    by_extension: list[ExtensionMetric] = Field(default_factory=list)


class FixPlanItem(BaseModel):
    priority: int
    category_id: str
    category_name: str
    check_id: str
    check_name: str
    status: CheckStatus
    impact_points: float
    action: str


class CheckDeltaItem(BaseModel):
    category_id: str
    check_id: str
    check_name: str
    previous_status: CheckStatus | None
    current_status: CheckStatus
    score_delta: float


class CategoryDeltaItem(BaseModel):
    category_id: str
    category_name: str
    previous_score: int
    current_score: int
    delta: int


class ReportComparison(BaseModel):
    previous_job_id: str | None = None
    previous_commit_sha: str | None = None
    current_commit_sha: str | None = None
    score_delta: int = 0
    categories: list[CategoryDeltaItem] = Field(default_factory=list)
    checks: list[CheckDeltaItem] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)
    changed_files_total: int = 0


class ReportSummary(BaseModel):
    job_id: str | None = None
    repo_owner: str
    repo_name: str
    repo_url: str
    generated_at: str
    score_total: int
    commit_sha: str | None = None
    detected_stacks: list[str] = Field(default_factory=list)
    project_metrics: ProjectMetrics
    categories: list[CategoryReport]
    fix_plan: list[FixPlanItem] = Field(default_factory=list)
    comparison: ReportComparison | None = None
    policy_issues: list[str] = Field(default_factory=list)
