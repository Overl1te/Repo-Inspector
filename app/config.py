"""Application configuration loader.

The project reads a public `config.yml` file and maps nested sections
to a typed `Settings` model.
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yml"


class Settings(BaseModel):
    """Runtime settings for API, GitHub integration and scan limits."""

    app_name: str = "Repo Inspector"
    app_logo_path: str = "/static/logo.png"
    app_title_separator: str = "В·"
    github_token: str = ""
    github_app_token: str = ""
    database_url: str = "sqlite:///./data/app.db"
    github_api_base: str = "https://api.github.com"
    scan_rate_limit_per_minute: int = 25
    scan_daily_quota: int = 300
    scan_cache_ttl_seconds: int = 1800
    repo_history_keep: int = 20
    stale_active_job_minutes: int = 120

    model_config = ConfigDict(extra="ignore")


def _read_yaml_config() -> dict[str, Any]:
    """Load `config.yml` into a dictionary.

    Returns an empty mapping when config file does not exist.
    """

    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as fp:
        raw = yaml.safe_load(fp) or {}
    if not isinstance(raw, dict):
        raise ValueError("config.yml root must be an object")
    return raw


def _extract_nested(raw: dict[str, Any]) -> dict[str, Any]:
    """Flatten nested config sections into `Settings` field names."""

    app = raw.get("app")
    github = raw.get("github")
    database = raw.get("database")
    scan = raw.get("scan")

    app_map = app if isinstance(app, dict) else {}
    github_map = github if isinstance(github, dict) else {}
    database_map = database if isinstance(database, dict) else {}
    scan_map = scan if isinstance(scan, dict) else {}

    return {
        "app_name": app_map.get("name", raw.get("app_name")),
        "app_logo_path": app_map.get("logo_path", raw.get("app_logo_path")),
        "app_title_separator": app_map.get("title_separator", raw.get("app_title_separator")),
        "github_token": github_map.get("token", raw.get("github_token")),
        "github_app_token": github_map.get("app_token", raw.get("github_app_token")),
        "github_api_base": github_map.get("api_base", raw.get("github_api_base")),
        "database_url": database_map.get("url", raw.get("database_url")),
        "scan_rate_limit_per_minute": scan_map.get(
            "rate_limit_per_minute",
            raw.get("scan_rate_limit_per_minute"),
        ),
        "scan_daily_quota": scan_map.get("daily_quota", raw.get("scan_daily_quota")),
        "scan_cache_ttl_seconds": scan_map.get("cache_ttl_seconds", raw.get("scan_cache_ttl_seconds")),
        "repo_history_keep": scan_map.get("repo_history_keep", raw.get("repo_history_keep")),
        "stale_active_job_minutes": scan_map.get(
            "stale_active_job_minutes",
            raw.get("stale_active_job_minutes"),
        ),
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance.

    Caching avoids repeated file I/O on every request.
    """

    raw = _read_yaml_config()
    values = {key: value for key, value in _extract_nested(raw).items() if value is not None}
    return Settings(**values)
