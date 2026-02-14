"""Repository-level policy parsing for `.repo-inspector.yml`."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Any

import yaml

from app.scanner.schemas import CheckResult

POLICY_PATHS = (
    ".repo-inspector.yml",
    ".repo-inspector.yaml",
    "repo-inspector.yml",
    "repo-inspector.yaml",
)


@dataclass
class RepoPolicy:
    """Validated policy configuration with defaults and validation errors."""

    readme_min_length: int = 200
    stale_days: int = 180
    category_weights: dict[str, int] = field(default_factory=dict)
    ignore_checks: set[str] = field(default_factory=set)
    baseline_min_score: int | None = None
    max_score_drop: int | None = None
    secret_allowlist_paths: list[str] = field(default_factory=list)
    secret_allowlist_patterns: list[str] = field(default_factory=list)
    validation_errors: list[str] = field(default_factory=list)
    source_path: str | None = None

    @property
    def is_valid(self) -> bool:
        """Whether policy has zero validation errors."""

        return not self.validation_errors

    def is_secret_allowed(self, path: str, token_value: str) -> bool:
        """Check whether secret match is allowlisted by path or prefix."""

        normalized = path.lower()
        if any(fnmatch(normalized, pattern.lower()) for pattern in self.secret_allowlist_paths):
            return True
        return any(token_value.startswith(prefix) for prefix in self.secret_allowlist_patterns)


def load_repo_policy(snapshot: Any) -> RepoPolicy:
    """Parse policy file from repository snapshot."""

    content = ""
    source_path: str | None = None
    for path in POLICY_PATHS:
        if path in snapshot.file_contents:
            content = snapshot.file_contents[path]
            source_path = path
            break
    if not content.strip():
        return RepoPolicy()

    policy = RepoPolicy(source_path=source_path)
    try:
        raw = yaml.safe_load(content) or {}
    except yaml.YAMLError as exc:
        policy.validation_errors.append(f"Invalid YAML: {exc}")
        return policy

    if not isinstance(raw, dict):
        policy.validation_errors.append("Policy must be a YAML mapping/object.")
        return policy

    allowed_keys = {"checks", "scoring", "baseline", "ignore", "security"}
    unknown_top = sorted(set(raw.keys()) - allowed_keys)
    if unknown_top:
        policy.validation_errors.append(f"Unknown top-level keys: {', '.join(unknown_top)}")

    checks_cfg = _as_dict(raw.get("checks"), "checks", policy)
    scoring_cfg = _as_dict(raw.get("scoring"), "scoring", policy)
    baseline_cfg = _as_dict(raw.get("baseline"), "baseline", policy)
    ignore_cfg = _as_dict(raw.get("ignore"), "ignore", policy)
    security_cfg = _as_dict(raw.get("security"), "security", policy)

    policy.readme_min_length = _as_int(checks_cfg.get("readme_min_length"), 200)
    policy.stale_days = _as_int(checks_cfg.get("stale_days"), 180)
    policy.category_weights = _normalize_category_weights(scoring_cfg.get("category_weights", {}), policy)
    policy.baseline_min_score = _as_optional_int(baseline_cfg.get("min_score"), policy, "baseline.min_score")
    policy.max_score_drop = _as_optional_int(
        baseline_cfg.get("max_score_drop"),
        policy,
        "baseline.max_score_drop",
    )
    policy.ignore_checks = _as_string_set(ignore_cfg.get("checks"), policy, "ignore.checks")
    policy.secret_allowlist_paths = _as_string_list(
        security_cfg.get("secret_allowlist_paths"),
        policy,
        "security.secret_allowlist_paths",
    )
    policy.secret_allowlist_patterns = _as_string_list(
        security_cfg.get("secret_allowlist_patterns"),
        policy,
        "security.secret_allowlist_patterns",
    )
    return policy


def apply_ignore_checks(
    checks_by_category: dict[str, list[CheckResult]],
    ignore_checks: set[str],
) -> dict[str, list[CheckResult]]:
    """Filter out checks that are explicitly ignored by policy."""

    if not ignore_checks:
        return checks_by_category
    filtered: dict[str, list[Any]] = {}
    for category, checks in checks_by_category.items():
        filtered[category] = [check for check in checks if check.id not in ignore_checks]
    return filtered


def _normalize_category_weights(raw: Any, policy: RepoPolicy) -> dict[str, int]:
    """Validate optional category weight overrides."""

    if not isinstance(raw, dict):
        if raw is not None:
            policy.validation_errors.append("scoring.category_weights must be an object")
        return {}
    allowed = {"docs", "ci", "security", "quality", "maintenance", "governance"}
    result: dict[str, int] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            policy.validation_errors.append("scoring.category_weights keys must be strings")
            continue
        lowered = key.lower()
        if lowered not in allowed:
            policy.validation_errors.append(f"Unknown category in weights: {key}")
            continue
        parsed = _as_int(value, -1)
        if parsed <= 0:
            policy.validation_errors.append(f"Weight for '{lowered}' must be positive integer")
            continue
        result[lowered] = parsed
    return result


def _as_dict(value: Any, field_name: str, policy: RepoPolicy) -> dict[str, Any]:
    """Coerce to dictionary and report validation error when invalid."""

    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    policy.validation_errors.append(f"'{field_name}' must be an object")
    return {}


def _as_string_set(value: Any, policy: RepoPolicy, field_name: str) -> set[str]:
    """Coerce to a set of non-empty strings."""

    if value is None:
        return set()
    if not isinstance(value, list):
        policy.validation_errors.append(f"'{field_name}' must be a list")
        return set()
    result = {item.strip() for item in value if isinstance(item, str) and item.strip()}
    non_str_count = len([item for item in value if not isinstance(item, str)])
    if non_str_count:
        policy.validation_errors.append(f"'{field_name}' has non-string values")
    return result


def _as_string_list(value: Any, policy: RepoPolicy, field_name: str) -> list[str]:
    """Coerce to list of non-empty strings while preserving order."""

    if value is None:
        return []
    if not isinstance(value, list):
        policy.validation_errors.append(f"'{field_name}' must be a list")
        return []
    items = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    if len(items) != len(value):
        policy.validation_errors.append(f"'{field_name}' must contain only non-empty strings")
    return items


def _as_int(value: Any, default: int) -> int:
    """Parse positive integer or return default."""

    try:
        parsed = int(value)
        return parsed if parsed > 0 else default
    except (TypeError, ValueError):
        return default


def _as_optional_int(value: Any, policy: RepoPolicy, field_name: str) -> int | None:
    """Parse optional non-negative integer with validation feedback."""

    if value is None:
        return None
    try:
        parsed = int(value)
        if parsed < 0:
            policy.validation_errors.append(f"'{field_name}' must be >= 0")
            return None
        return parsed
    except (TypeError, ValueError):
        policy.validation_errors.append(f"'{field_name}' must be an integer")
        return None
