"""FastAPI application entrypoint for Repo Inspector."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections import defaultdict, deque
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import Base, SessionLocal, engine, ensure_sqlite_compat_schema, get_db
from app.github_client import GitHubAPIError, GitHubClient, RepoPublicStats
from app.models import ScanJob, ScanReport
from app.scanner.checks import detect_stacks, project_line_metrics, run_all_checks
from app.scanner.i18n import get_client_i18n, get_ui_labels, localize_report, normalize_lang
from app.scanner.policy import RepoPolicy, load_repo_policy
from app.scanner.schemas import CategoryDeltaItem, CheckDeltaItem, CheckResult, ReportComparison
from app.scanner.scoring import build_report, check_weight_map
from app.stats_card import build_quality_stats_svg, build_repo_stats_svg
from app.theme_store import THEME_KEYS, get_custom_theme_defaults, get_theme_options

GITHUB_REPO_RE = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s#]+?)(?:\.git)?/?$")
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.2.0")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

_RATE_WINDOW_SECONDS = 60
_REPO_STATS_CACHE_TTL_SECONDS = 300
_QUALITY_LIVE_CACHE_TTL_SECONDS = 180
_LIVE_SNAPSHOT_LINE_COUNT_FETCH_LIMIT = 120
_scan_requests: dict[str, deque[float]] = defaultdict(deque)
_scan_daily_usage: dict[str, tuple[date, int]] = {}
_repo_stats_cache: dict[str, tuple[float, RepoPublicStats]] = {}
_quality_live_cache: dict[str, tuple[float, dict[str, object]]] = {}
_started_at = time.time()
_metrics: dict[str, float] = {
    "http_requests_total": 0,
    "http_request_errors_total": 0,
    "scan_jobs_started_total": 0,
    "scan_jobs_done_total": 0,
    "scan_jobs_failed_total": 0,
    "scan_jobs_cached_total": 0,
    "github_api_errors_total": 0,
}
_PAGES_HOME_URL = os.getenv("RQI_PUBLIC_WEB_URL", "https://overl1te.github.io/Repo-Inspector/")
_PAGES_GENERATOR_URL = os.getenv(
    "RQI_PUBLIC_GENERATOR_URL",
    f"{_PAGES_HOME_URL.rstrip('/')}/generator.html",
)


class ScanRequest(BaseModel):
    """Request body for creating a new scan job."""

    repo_url: str
    github_token: str | None = None

    @field_validator("repo_url")
    @classmethod
    def validate_repo_url(cls, value: str) -> str:
        if not GITHUB_REPO_RE.match(value.strip()):
            raise ValueError("URL must be in format https://github.com/<owner>/<repo>")
        return value.strip()

    @field_validator("github_token")
    @classmethod
    def validate_github_token(cls, value: str | None) -> str | None:
        if value is None:
            return None
        token = value.strip()
        return token or None


@app.on_event("startup")
def on_startup() -> None:
    """Initialize DB schema and compatibility migrations."""

    Base.metadata.create_all(bind=engine)
    ensure_sqlite_compat_schema()


@app.middleware("http")
async def collect_http_metrics(request: Request, call_next: Any) -> Any:
    """Collect basic request/exception counters for `/metrics`."""

    _metrics["http_requests_total"] += 1
    try:
        return await call_next(request)
    except Exception:
        _metrics["http_request_errors_total"] += 1
        raise


def parse_repo_url(repo_url: str) -> tuple[str, str]:
    """Parse repository owner/name from GitHub URL."""

    match = GITHUB_REPO_RE.match(repo_url.strip())
    if not match:
        raise ValueError("Invalid GitHub repository URL.")
    return match.group(1), match.group(2)


def site_template_context() -> dict[str, str]:
    """Return global branding fields passed to templates."""

    return {
        "app_name": settings.app_name,
        "logo_path": settings.app_logo_path,
        "title_separator": settings.app_title_separator,
    }


def _is_vercel_runtime() -> bool:
    return bool(os.getenv("VERCEL"))


def _lang_url(url: str, lang: str) -> str:
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}lang={lang}"


def _backend_landing_page(lang: str) -> str:
    home_url = _lang_url(_PAGES_HOME_URL, lang)
    generator_url = _lang_url(_PAGES_GENERATOR_URL, lang)
    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{settings.app_name} - API endpoint</title>
  <meta http-equiv="refresh" content="3; url={generator_url}">
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f9ff;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --accent: #2563eb;
      --line: #dbeafe;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      background: radial-gradient(900px 400px at 50% -10%, #dbeafe 0%, transparent 65%), var(--bg);
      font-family: "Segoe UI", sans-serif;
      color: var(--text);
      padding: 1rem;
    }}
    .card {{
      max-width: 620px;
      width: 100%;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 1.15rem;
      box-shadow: 0 12px 34px rgba(15, 23, 42, 0.08);
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: 1.28rem;
    }}
    p {{
      margin: 0 0 0.64rem;
      color: var(--muted);
      line-height: 1.45;
    }}
    .actions {{
      display: flex;
      gap: 0.6rem;
      flex-wrap: wrap;
      margin-top: 0.9rem;
    }}
    a {{
      display: inline-block;
      padding: 0.56rem 0.9rem;
      border-radius: 10px;
      text-decoration: none;
      font-weight: 700;
      border: 1px solid var(--line);
      color: var(--accent);
      background: #eff6ff;
    }}
  </style>
</head>
<body>
  <main class="card">
    <h1>{settings.app_name} backend</h1>
    <p>This domain serves API only.</p>
    <p>Open the web app and generator on GitHub Pages.</p>
    <div class="actions">
      <a href="{home_url}">Open web app</a>
      <a href="{generator_url}">Open generator</a>
    </div>
  </main>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, lang: str = "en") -> HTMLResponse:
    lang = normalize_lang(lang)
    if _is_vercel_runtime():
        return HTMLResponse(content=_backend_landing_page(lang))
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "lang": lang,
            "ui": get_ui_labels(lang),
            "client_i18n": get_client_i18n(),
            "site": site_template_context(),
        },
    )


@app.get("/generator", response_class=HTMLResponse)
async def svg_generator(request: Request, lang: str = "en") -> HTMLResponse:
    lang = normalize_lang(lang)
    if _is_vercel_runtime():
        return RedirectResponse(url=_lang_url(_PAGES_GENERATOR_URL, lang), status_code=307)
    ui = get_ui_labels(lang)
    themes = get_theme_options(ui)
    return templates.TemplateResponse(
        "generator.html",
        {
            "request": request,
            "lang": lang,
            "ui": ui,
            "client_i18n": get_client_i18n(),
            "themes": themes,
            "custom_theme_defaults": get_custom_theme_defaults(),
            "site": site_template_context(),
        },
    )


@app.get("/jobs/{job_id}", response_class=HTMLResponse)
async def progress_page(
    request: Request,
    job_id: str,
    lang: str = "en",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    lang = normalize_lang(lang)
    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return templates.TemplateResponse(
        "progress.html",
        {
            "request": request,
            "job": job,
            "lang": lang,
            "ui": get_ui_labels(lang),
            "client_i18n": get_client_i18n(),
            "site": site_template_context(),
        },
    )


@app.post("/api/scan")
async def start_scan(
    request: Request,
    payload: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Create scan job and dispatch background processing."""

    _enforce_scan_access_limits(request)
    owner, repo = parse_repo_url(payload.repo_url)
    _expire_stale_active_jobs(db, owner, repo)

    active_job = (
        db.query(ScanJob)
        .filter(
            ScanJob.repo_owner == owner,
            ScanJob.repo_name == repo,
            ScanJob.status.in_(["queued", "running"]),
        )
        .order_by(ScanJob.created_at.desc())
        .first()
    )
    if active_job:
        return {"job_id": active_job.id, "status": active_job.status}

    try:
        access_client = GitHubClient(token=payload.github_token)
        await access_client.check_repo_access(owner, repo)
    except GitHubAPIError as exc:
        if _is_github_not_found_error(exc):
            raise HTTPException(
                status_code=404,
                detail=(
                    "Repository not found. If this repository is private, provide a GitHub token "
                    "and try again. Token is used only for this scan and is never stored."
                ),
            ) from exc
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    job = ScanJob(repo_owner=owner, repo_name=repo, repo_url=payload.repo_url, status="queued", progress=0)
    db.add(job)
    db.commit()
    db.refresh(job)
    _metrics["scan_jobs_started_total"] += 1
    background_tasks.add_task(run_scan_job, job.id, payload.github_token)
    return {"job_id": job.id, "status": job.status}


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str, lang: str = "en", db: Session = Depends(get_db)) -> JSONResponse:
    lang = normalize_lang(lang)
    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    result: dict[str, object] = {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message,
    }
    if job.status == "done" and job.report:
        report_payload = localize_report(json.loads(job.report.report_json), lang)
        result["summary"] = {
            "repo_url": report_payload.get("repo_url"),
            "score_total": report_payload.get("score_total"),
            "detected_stacks": report_payload.get("detected_stacks", []),
            "total_code_lines": (report_payload.get("project_metrics", {}) or {}).get("total_code_lines", 0),
        }
        result["report_url"] = f"/report/{job.id}?lang={lang}"
        result["report_json_url"] = f"/api/report/{job.id}.json?lang={lang}"
    return JSONResponse(result)


@app.get("/report/{job_id}", response_class=HTMLResponse)
async def report_page(
    request: Request,
    job_id: str,
    lang: str = "en",
    db: Session = Depends(get_db),
) -> HTMLResponse:
    lang = normalize_lang(lang)
    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done" or not job.report:
        return RedirectResponse(url=f"/jobs/{job_id}?lang={lang}", status_code=302)

    report = localize_report(json.loads(job.report.report_json), lang)
    history = _repo_history(db, job.repo_owner, job.repo_name, limit=30)
    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "job": job,
            "report": report,
            "history": history,
            "history_json": json.dumps(history),
            "lang": lang,
            "ui": get_ui_labels(lang),
            "client_i18n": get_client_i18n(),
            "site": site_template_context(),
        },
    )


@app.get("/api/report/{job_id}.json")
async def report_json(job_id: str, lang: str = "en", db: Session = Depends(get_db)) -> JSONResponse:
    payload = _report_payload(db, job_id)
    return JSONResponse(content=localize_report(payload, normalize_lang(lang)))


@app.get("/api/report/{job_id}.md")
async def report_markdown(job_id: str, lang: str = "en", db: Session = Depends(get_db)) -> PlainTextResponse:
    normalized_lang = normalize_lang(lang)
    payload = localize_report(_report_payload(db, job_id), normalized_lang)
    return PlainTextResponse(
        _report_to_markdown(payload, normalized_lang),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="report-{job_id}.md"'},
    )


@app.get("/api/report/{job_id}.txt")
async def report_text(job_id: str, lang: str = "en", db: Session = Depends(get_db)) -> PlainTextResponse:
    normalized_lang = normalize_lang(lang)
    payload = localize_report(_report_payload(db, job_id), normalized_lang)
    return PlainTextResponse(
        _report_to_markdown(payload, normalized_lang),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="report-{job_id}.txt"'},
    )


@app.get("/api/repos/{owner}/{repo}/history")
async def repo_history(owner: str, repo: str, db: Session = Depends(get_db)) -> JSONResponse:
    return JSONResponse({"owner": owner, "repo": repo, "history": _repo_history(db, owner, repo, limit=50)})


@app.get("/api/repos/{owner}/{repo}/latest")
async def repo_latest(owner: str, repo: str, db: Session = Depends(get_db)) -> JSONResponse:
    row = (
        db.query(ScanJob.id, ScanJob.commit_sha, ScanJob.finished_at, ScanReport.score_total)
        .join(ScanReport, ScanReport.job_id == ScanJob.id)
        .filter(ScanJob.repo_owner == owner, ScanJob.repo_name == repo, ScanJob.status == "done")
        .order_by(ScanJob.finished_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="No reports found")
    return JSONResponse(
        {
            "job_id": row[0],
            "commit_sha": row[1],
            "finished_at": row[2].isoformat() if row[2] else None,
            "score_total": row[3],
            "report_url": f"/report/{row[0]}",
        }
    )


@app.get("/api/stats/repo/{owner}/{repo}.json")
async def repo_stats_json(
    owner: str,
    repo: str,
    fields: str | None = None,
    langs_count: int = Query(default=10, ge=1, le=30),
) -> JSONResponse:
    payload = await _build_public_repo_stats_payload(owner, repo, langs_count=langs_count)
    if fields:
        repository_raw = payload.get("repository")
        if isinstance(repository_raw, dict):
            payload["repository"] = _select_dict_fields(repository_raw, fields)
    return JSONResponse(payload)


@app.api_route("/api/stats/repo/{owner}/{repo}.svg", methods=["GET", "HEAD"])
async def repo_stats_svg(
    request: Request,
    owner: str,
    repo: str,
    theme: str = "ocean",
    locale: str = "en",
    hide: str | None = None,
    title: str | None = None,
    card_width: int = Query(default=760, ge=640, le=1400),
    langs_count: int = Query(default=4, ge=1, le=10),
    animate: bool = False,
    animation: str = "all",
    duration: int = Query(default=1400, ge=350, le=7000),
    bg_start: str | None = Query(default=None),
    bg_end: str | None = Query(default=None),
    border: str | None = Query(default=None),
    panel: str | None = Query(default=None),
    overlay: str | None = Query(default=None),
    chip_bg: str | None = Query(default=None),
    chip_text: str | None = Query(default=None),
    text: str | None = Query(default=None),
    muted: str | None = Query(default=None),
    accent: str | None = Query(default=None),
    accent_2: str | None = Query(default=None),
    accent_soft: str | None = Query(default=None),
    track: str | None = Query(default=None),
    pass_color: str | None = Query(default=None, alias="pass"),
    warn: str | None = Query(default=None),
    fail: str | None = Query(default=None),
    cache_seconds: int = Query(default=21600, ge=0, le=86400),
) -> Response:
    if request.method == "HEAD":
        return Response(content=b"", media_type="image/svg+xml", headers=_svg_cache_headers(cache_seconds))

    payload = await _build_public_repo_stats_payload(owner, repo, langs_count=max(4, langs_count))
    hidden = _parse_csv_flags(hide)
    custom_theme = _collect_custom_theme(
        {
            "bg_start": bg_start,
            "bg_end": bg_end,
            "border": border,
            "panel": panel,
            "overlay": overlay,
            "chip_bg": chip_bg,
            "chip_text": chip_text,
            "text": text,
            "muted": muted,
            "accent": accent,
            "accent_2": accent_2,
            "accent_soft": accent_soft,
            "track": track,
            "pass": pass_color,
            "warn": warn,
            "fail": fail,
        }
    )
    svg = build_repo_stats_svg(
        payload,
        theme=theme,
        custom_theme=custom_theme,
        locale=normalize_lang(locale),
        card_width=card_width,
        langs_count=langs_count,
        hide=hidden,
        title=title,
        animate=animate,
        animation=animation,
        duration_ms=duration,
    )
    headers = _svg_cache_headers(cache_seconds)
    return Response(content=svg, media_type="image/svg+xml", headers=headers)


@app.api_route("/api", methods=["GET", "HEAD"])
async def readme_stats_api(
    request: Request,
    owner: str | None = None,
    repo: str | None = None,
    kind: str = Query(default="repo", pattern="^(repo|quality)$"),
    format: str = Query(default="svg", pattern="^(svg|json)$"),
    theme: str = "ocean",
    locale: str = "en",
    hide: str | None = None,
    title: str | None = None,
    card_width: int = Query(default=760, ge=640, le=1400),
    langs_count: int = Query(default=4, ge=1, le=10),
    animate: bool = False,
    animation: str = "all",
    duration: int = Query(default=1400, ge=350, le=7000),
    bg_start: str | None = Query(default=None),
    bg_end: str | None = Query(default=None),
    border: str | None = Query(default=None),
    panel: str | None = Query(default=None),
    overlay: str | None = Query(default=None),
    chip_bg: str | None = Query(default=None),
    chip_text: str | None = Query(default=None),
    text: str | None = Query(default=None),
    muted: str | None = Query(default=None),
    accent: str | None = Query(default=None),
    accent_2: str | None = Query(default=None),
    accent_soft: str | None = Query(default=None),
    track: str | None = Query(default=None),
    pass_color: str | None = Query(default=None, alias="pass"),
    warn: str | None = Query(default=None),
    fail: str | None = Query(default=None),
    cache_seconds: int = Query(default=21600, ge=0, le=86400),
    fields: str | None = None,
    include_report: bool = False,
    db: Session = Depends(get_db),
) -> Response:
    """Readme-stats style endpoint.

    Examples:
    - `/api?owner=octocat&repo=Hello-World&kind=repo`
    - `/api?owner=octocat&repo=Hello-World&kind=quality&format=json`
    """

    if not owner or not repo:
        raise HTTPException(status_code=400, detail="Use query params: owner=<owner>&repo=<repo>")

    if request.method == "HEAD":
        if format == "svg":
            return Response(content=b"", media_type="image/svg+xml", headers=_svg_cache_headers(cache_seconds))
        return Response(content=b"", media_type="application/json")

    normalized_locale = normalize_lang(locale)
    hidden = _parse_csv_flags(hide)
    custom_theme = _collect_custom_theme(
        {
            "bg_start": bg_start,
            "bg_end": bg_end,
            "border": border,
            "panel": panel,
            "overlay": overlay,
            "chip_bg": chip_bg,
            "chip_text": chip_text,
            "text": text,
            "muted": muted,
            "accent": accent,
            "accent_2": accent_2,
            "accent_soft": accent_soft,
            "track": track,
            "pass": pass_color,
            "warn": warn,
            "fail": fail,
        }
    )

    if format == "json":
        if kind == "quality":
            payload = await _build_quality_stats_payload(owner, repo, db, include_report=include_report)
            payload = _localize_quality_payload(payload, normalized_locale)
            if fields:
                quality_raw = payload.get("quality")
                if isinstance(quality_raw, dict):
                    payload["quality"] = _select_dict_fields(quality_raw, fields)
        else:
            payload = await _build_public_repo_stats_payload(owner, repo, langs_count=max(1, langs_count))
            if fields:
                repository_raw = payload.get("repository")
                if isinstance(repository_raw, dict):
                    payload["repository"] = _select_dict_fields(repository_raw, fields)
        return JSONResponse(payload)

    if kind == "quality":
        payload = await _build_quality_stats_payload(owner, repo, db, include_report=False)
        svg = build_quality_stats_svg(
            payload,
            theme=theme,
            custom_theme=custom_theme,
            locale=normalized_locale,
            card_width=card_width,
            hide=hidden,
            title=title,
            animate=animate,
            animation=animation,
            duration_ms=duration,
        )
    else:
        payload = await _build_public_repo_stats_payload(owner, repo, langs_count=max(4, langs_count))
        svg = build_repo_stats_svg(
            payload,
            theme=theme,
            custom_theme=custom_theme,
            locale=normalized_locale,
            card_width=card_width,
            langs_count=langs_count,
            hide=hidden,
            title=title,
            animate=animate,
            animation=animation,
            duration_ms=duration,
        )
    headers = _svg_cache_headers(cache_seconds)
    return Response(content=svg, media_type="image/svg+xml", headers=headers)


@app.get("/api/stats/quality/{owner}/{repo}.json")
async def quality_stats_json(
    owner: str,
    repo: str,
    db: Session = Depends(get_db),
    fields: str | None = None,
    include_report: bool = False,
    locale: str = "en",
) -> JSONResponse:
    payload = await _build_quality_stats_payload(owner, repo, db, include_report=include_report)
    payload = _localize_quality_payload(payload, normalize_lang(locale))
    if fields:
        quality_raw = payload.get("quality")
        if isinstance(quality_raw, dict):
            payload["quality"] = _select_dict_fields(quality_raw, fields)
    return JSONResponse(payload)


@app.api_route("/api/stats/quality/{owner}/{repo}.svg", methods=["GET", "HEAD"])
async def quality_stats_svg(
    request: Request,
    owner: str,
    repo: str,
    db: Session = Depends(get_db),
    theme: str = "ocean",
    locale: str = "en",
    hide: str | None = None,
    title: str | None = None,
    card_width: int = Query(default=760, ge=640, le=1400),
    animate: bool = False,
    animation: str = "all",
    duration: int = Query(default=1400, ge=350, le=7000),
    bg_start: str | None = Query(default=None),
    bg_end: str | None = Query(default=None),
    border: str | None = Query(default=None),
    panel: str | None = Query(default=None),
    overlay: str | None = Query(default=None),
    chip_bg: str | None = Query(default=None),
    chip_text: str | None = Query(default=None),
    text: str | None = Query(default=None),
    muted: str | None = Query(default=None),
    accent: str | None = Query(default=None),
    accent_2: str | None = Query(default=None),
    accent_soft: str | None = Query(default=None),
    track: str | None = Query(default=None),
    pass_color: str | None = Query(default=None, alias="pass"),
    warn: str | None = Query(default=None),
    fail: str | None = Query(default=None),
    cache_seconds: int = Query(default=300, ge=0, le=86400),
) -> Response:
    if request.method == "HEAD":
        return Response(content=b"", media_type="image/svg+xml", headers=_svg_cache_headers(cache_seconds))

    payload = await _build_quality_stats_payload(owner, repo, db, include_report=False)
    hidden = _parse_csv_flags(hide)
    custom_theme = _collect_custom_theme(
        {
            "bg_start": bg_start,
            "bg_end": bg_end,
            "border": border,
            "panel": panel,
            "overlay": overlay,
            "chip_bg": chip_bg,
            "chip_text": chip_text,
            "text": text,
            "muted": muted,
            "accent": accent,
            "accent_2": accent_2,
            "accent_soft": accent_soft,
            "track": track,
            "pass": pass_color,
            "warn": warn,
            "fail": fail,
        }
    )
    svg = build_quality_stats_svg(
        payload,
        theme=theme,
        custom_theme=custom_theme,
        locale=normalize_lang(locale),
        card_width=card_width,
        hide=hidden,
        title=title,
        animate=animate,
        animation=animation,
        duration_ms=duration,
    )
    headers = _svg_cache_headers(cache_seconds)
    return Response(content=svg, media_type="image/svg+xml", headers=headers)


@app.get("/api/stats/{owner}/{repo}.json")
async def legacy_stats_json(owner: str, repo: str, db: Session = Depends(get_db)) -> JSONResponse:
    payload = await _build_combined_stats_payload(owner, repo, db)
    return JSONResponse(payload)


@app.api_route("/api/stats/{owner}/{repo}.svg", methods=["GET", "HEAD"])
async def legacy_stats_svg(
    request: Request,
    owner: str,
    repo: str,
    db: Session = Depends(get_db),
    theme: str = "ocean",
    locale: str = "en",
    hide: str | None = None,
    title: str | None = None,
    card_width: int = Query(default=760, ge=640, le=1400),
    langs_count: int = Query(default=4, ge=1, le=10),
    animate: bool = False,
    animation: str = "all",
    duration: int = Query(default=1400, ge=350, le=7000),
    bg_start: str | None = Query(default=None),
    bg_end: str | None = Query(default=None),
    border: str | None = Query(default=None),
    panel: str | None = Query(default=None),
    overlay: str | None = Query(default=None),
    chip_bg: str | None = Query(default=None),
    chip_text: str | None = Query(default=None),
    text: str | None = Query(default=None),
    muted: str | None = Query(default=None),
    accent: str | None = Query(default=None),
    accent_2: str | None = Query(default=None),
    accent_soft: str | None = Query(default=None),
    track: str | None = Query(default=None),
    pass_color: str | None = Query(default=None, alias="pass"),
    warn: str | None = Query(default=None),
    fail: str | None = Query(default=None),
    cache_seconds: int = Query(default=21600, ge=0, le=86400),
) -> Response:
    if request.method == "HEAD":
        return Response(content=b"", media_type="image/svg+xml", headers=_svg_cache_headers(cache_seconds))

    payload = await _build_combined_stats_payload(owner, repo, db)
    hidden = _parse_csv_flags(hide)
    custom_theme = _collect_custom_theme(
        {
            "bg_start": bg_start,
            "bg_end": bg_end,
            "border": border,
            "panel": panel,
            "overlay": overlay,
            "chip_bg": chip_bg,
            "chip_text": chip_text,
            "text": text,
            "muted": muted,
            "accent": accent,
            "accent_2": accent_2,
            "accent_soft": accent_soft,
            "track": track,
            "pass": pass_color,
            "warn": warn,
            "fail": fail,
        }
    )
    svg = build_repo_stats_svg(
        payload,
        theme=theme,
        custom_theme=custom_theme,
        locale=normalize_lang(locale),
        card_width=card_width,
        langs_count=langs_count,
        hide=hidden,
        title=title,
        animate=animate,
        animation=animation,
        duration_ms=duration,
    )
    headers = _svg_cache_headers(cache_seconds)
    return Response(content=svg, media_type="image/svg+xml", headers=headers)


@app.get("/api/compare/{job_id}/{previous_job_id}")
async def compare_reports(job_id: str, previous_job_id: str, db: Session = Depends(get_db)) -> JSONResponse:
    current_payload = _report_payload(db, job_id)
    previous_payload = _report_payload(db, previous_job_id)
    comparison = _build_report_comparison(
        {
            "job_id": previous_job_id,
            "commit_sha": previous_payload.get("commit_sha"),
            "payload": previous_payload,
        },
        current_payload,
        [],
        current_payload.get("commit_sha"),
    )
    return JSONResponse(content=comparison.model_dump(mode="json"))


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "version": app.version,
            "uptime_seconds": round(time.time() - _started_at, 2),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    lines = [
        "# TYPE rqi_http_requests_total counter",
        f"rqi_http_requests_total {_metrics['http_requests_total']}",
        "# TYPE rqi_http_request_errors_total counter",
        f"rqi_http_request_errors_total {_metrics['http_request_errors_total']}",
        "# TYPE rqi_scan_jobs_started_total counter",
        f"rqi_scan_jobs_started_total {_metrics['scan_jobs_started_total']}",
        "# TYPE rqi_scan_jobs_done_total counter",
        f"rqi_scan_jobs_done_total {_metrics['scan_jobs_done_total']}",
        "# TYPE rqi_scan_jobs_failed_total counter",
        f"rqi_scan_jobs_failed_total {_metrics['scan_jobs_failed_total']}",
        "# TYPE rqi_scan_jobs_cached_total counter",
        f"rqi_scan_jobs_cached_total {_metrics['scan_jobs_cached_total']}",
        "# TYPE rqi_github_api_errors_total counter",
        f"rqi_github_api_errors_total {_metrics['github_api_errors_total']}",
    ]
    return PlainTextResponse("\n".join(lines) + "\n")


def run_scan_job(job_id: str, github_token: str | None = None) -> None:
    """Bridge sync BackgroundTasks callback to async scanner."""

    asyncio.run(scan_job_async(job_id, github_token))


async def scan_job_async(job_id: str, github_token: str | None = None) -> None:
    """Execute one scan job lifecycle and persist final report."""

    db = SessionLocal()
    try:
        job = db.get(ScanJob, job_id)
        if not job:
            return
        owner, repo = job.repo_owner, job.repo_name
        job.status, job.started_at, job.progress, job.error_message = "running", datetime.now(UTC), 10, None
        db.commit()
    finally:
        db.close()

    try:
        client = GitHubClient(token=github_token)
        snapshot = await client.get_repo_snapshot(owner, repo)
        cached_payload = _find_cached_report_for_commit(
            snapshot.owner,
            snapshot.name,
            snapshot.default_branch_sha,
            job_id,
        )
        if cached_payload is not None:
            _metrics["scan_jobs_cached_total"] += 1
            cached_payload["generated_at"] = datetime.now(UTC).isoformat()
            cached_payload["job_id"] = job_id
            cached_payload["commit_sha"] = snapshot.default_branch_sha
            _finalize_success_job(
                job_id,
                snapshot.owner,
                snapshot.name,
                snapshot.default_branch_sha,
                cached_payload,
            )
            return

        db_mid = SessionLocal()
        try:
            job_mid = db_mid.get(ScanJob, job_id)
            if job_mid:
                job_mid.progress = 65
                db_mid.commit()
        finally:
            db_mid.close()

        policy = load_repo_policy(snapshot)
        checks = run_all_checks(snapshot, enable_network=True, policy=policy)
        stacks = detect_stacks(snapshot)
        metrics = project_line_metrics(snapshot)
        previous = _latest_previous_report(snapshot.owner, snapshot.name, job_id)
        prev_score = _extract_previous_score(previous)
        provisional = build_report(
            repo_owner=snapshot.owner,
            repo_name=snapshot.name,
            repo_url=snapshot.url,
            checks_by_category=checks,
            project_metrics=metrics,
            detected_stacks=stacks,
            category_weights=policy.category_weights,
            job_id=job_id,
            commit_sha=snapshot.default_branch_sha,
            policy_issues=policy.validation_errors,
        )
        guard = _score_regression_check(prev_score, provisional.score_total, policy)
        if guard:
            checks.setdefault("governance", []).append(guard)

        report = build_report(
            repo_owner=snapshot.owner,
            repo_name=snapshot.name,
            repo_url=snapshot.url,
            checks_by_category=checks,
            project_metrics=metrics,
            detected_stacks=stacks,
            category_weights=policy.category_weights,
            job_id=job_id,
            commit_sha=snapshot.default_branch_sha,
            policy_issues=policy.validation_errors,
        )
        changed_files: list[str] = []
        if previous and snapshot.default_branch_sha and previous.get("commit_sha"):
            try:
                changed_files = await client.get_changed_files_between_commits(
                    snapshot.owner,
                    snapshot.name,
                    str(previous.get("commit_sha")),
                    snapshot.default_branch_sha,
                )
            except GitHubAPIError:
                changed_files = []

        report_dict = report.model_dump(mode="json")
        report.comparison = _build_report_comparison(
            previous,
            report_dict,
            changed_files,
            snapshot.default_branch_sha,
        )
        _finalize_success_job(
            job_id,
            snapshot.owner,
            snapshot.name,
            snapshot.default_branch_sha,
            report.model_dump(mode="json"),
        )
    except GitHubAPIError as exc:
        _metrics["github_api_errors_total"] += 1
        _mark_failed(job_id, str(exc))
    except Exception as exc:  # pragma: no cover
        _mark_failed(job_id, f"Unexpected error while scanning repository: {exc}")


async def _build_combined_stats_payload(owner: str, repo: str, db: Session) -> dict[str, object]:
    repo_payload = await _build_public_repo_stats_payload(owner, repo, langs_count=10)
    quality = _latest_repo_quality_snapshot(db, owner, repo, include_report=False)
    if quality is None:
        quality = await _build_live_quality_snapshot(owner, repo, include_report=False)
    payload: dict[str, object] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": repo_payload["repository"],
        "quality": quality,
        "links": {
            "repo_json": f"/api/stats/repo/{owner}/{repo}.json",
            "repo_svg": f"/api/stats/repo/{owner}/{repo}.svg",
            "quality_json": f"/api/stats/quality/{owner}/{repo}.json",
            "quality_svg": f"/api/stats/quality/{owner}/{repo}.svg",
        },
    }
    if quality and isinstance(quality.get("report_url"), str):
        payload["latest_report_url"] = quality["report_url"]
    return payload


async def _build_public_repo_stats_payload(owner: str, repo: str, langs_count: int = 10) -> dict[str, object]:
    client = GitHubClient()
    cache_key = f"{owner.strip().lower()}/{repo.strip().lower()}"
    cached = _repo_stats_cache.get(cache_key)
    repo_stats: RepoPublicStats | None = None
    if cached and (time.time() - cached[0]) <= _REPO_STATS_CACHE_TTL_SECONDS:
        repo_stats = cached[1]
    try:
        if repo_stats is None:
            repo_stats = await client.get_repo_public_stats(owner, repo)
            _repo_stats_cache[cache_key] = (time.time(), repo_stats)
    except GitHubAPIError as exc:
        if cached:
            repo_stats = cached[1]
        else:
            raise _github_error_to_http(exc) from exc
    if repo_stats is None:
        raise HTTPException(status_code=500, detail="Failed to build repository stats payload")

    repo_data = _serialize_repo_stats(repo_stats)
    languages = repo_data.get("languages")
    if isinstance(languages, list):
        repo_data["languages"] = languages[: max(1, langs_count)]
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": repo_data,
        "links": {
            "json": f"/api/stats/repo/{owner}/{repo}.json",
            "svg": f"/api/stats/repo/{owner}/{repo}.svg",
        },
    }


async def _build_quality_stats_payload(
    owner: str,
    repo: str,
    db: Session,
    include_report: bool = False,
) -> dict[str, object]:
    quality = _latest_repo_quality_snapshot(db, owner, repo, include_report=include_report)
    if quality is None:
        quality = await _build_live_quality_snapshot(owner, repo, include_report=include_report)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "repository": {
            "owner": owner,
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "html_url": f"https://github.com/{owner}/{repo}",
        },
        "quality": quality,
        "links": {
            "json": f"/api/stats/quality/{owner}/{repo}.json",
            "svg": f"/api/stats/quality/{owner}/{repo}.svg",
            "report": quality.get("report_url"),
        },
    }


async def _build_live_quality_snapshot(
    owner: str,
    repo: str,
    include_report: bool = False,
) -> dict[str, object]:
    """Compute quality snapshot on demand without persisted scan history."""

    cache_key = (
        f"{owner.strip().lower()}/{repo.strip().lower()}"
        f"/report={1 if include_report else 0}"
    )
    cached_entry = _quality_live_cache.get(cache_key)
    cached_payload = cached_entry[1] if cached_entry else None
    if cached_entry and (time.time() - cached_entry[0]) <= _QUALITY_LIVE_CACHE_TTL_SECONDS:
        return json.loads(json.dumps(cached_entry[1]))

    client = GitHubClient()
    try:
        line_count_fetch_limit = None if include_report else _LIVE_SNAPSHOT_LINE_COUNT_FETCH_LIMIT
        snapshot = await client.get_repo_snapshot(
            owner,
            repo,
            line_count_fetch_limit=line_count_fetch_limit,
        )
    except GitHubAPIError as exc:
        if isinstance(cached_payload, dict):
            return json.loads(json.dumps(cached_payload))
        raise _github_error_to_http(exc) from exc

    policy = load_repo_policy(snapshot)
    checks = run_all_checks(snapshot, enable_network=False, policy=policy)
    stacks = detect_stacks(snapshot)
    metrics = project_line_metrics(snapshot)
    report = build_report(
        repo_owner=snapshot.owner,
        repo_name=snapshot.name,
        repo_url=snapshot.url,
        checks_by_category=checks,
        project_metrics=metrics,
        detected_stacks=stacks,
        category_weights=policy.category_weights,
        commit_sha=snapshot.default_branch_sha,
        policy_issues=policy.validation_errors,
    )
    report_payload = report.model_dump(mode="json")
    status_counts = {"pass": 0, "warn": 0, "fail": 0}
    category_scores: list[dict[str, object]] = []
    for category in report.categories:
        category_scores.append(
            {
                "id": category.id,
                "name": category.name,
                "score": int(category.score),
                "weight": int(category.weight),
            }
        )
        for check in category.checks:
            if check.status in status_counts:
                status_counts[check.status] += 1

    result: dict[str, object] = {
        "job_id": None,
        "commit_sha": snapshot.default_branch_sha,
        "finished_at": datetime.now(UTC).isoformat(),
        "score_total": int(report.score_total),
        "report_url": None,
        "total_code_lines": int(report.project_metrics.total_code_lines),
        "total_code_files": int(report.project_metrics.total_code_files),
        "scanned_code_files": int(report.project_metrics.scanned_code_files),
        "status_counts": status_counts,
        "category_scores": category_scores,
        "detected_stacks": [str(stack) for stack in stacks[:20]],
        "source": "live",
    }
    if include_report:
        result["report"] = report_payload
    _quality_live_cache[cache_key] = (time.time(), result)
    return json.loads(json.dumps(result))


def _serialize_repo_stats(repo_stats: RepoPublicStats) -> dict[str, object]:
    language_total_bytes = sum(repo_stats.languages.values())
    languages = [
        {"name": name, "bytes": amount}
        for name, amount in sorted(repo_stats.languages.items(), key=lambda item: item[1], reverse=True)
    ]
    return {
        "owner": repo_stats.owner,
        "name": repo_stats.name,
        "full_name": repo_stats.full_name,
        "html_url": repo_stats.html_url,
        "description": repo_stats.description,
        "stars": repo_stats.stars,
        "forks": repo_stats.forks,
        "open_issues": repo_stats.open_issues,
        "watchers": repo_stats.watchers,
        "default_branch": repo_stats.default_branch,
        "primary_language": repo_stats.primary_language,
        "license_name": repo_stats.license_name,
        "topics": repo_stats.topics,
        "archived": repo_stats.archived,
        "is_fork": repo_stats.is_fork,
        "size_kb": repo_stats.size_kb,
        "created_at": repo_stats.created_at.isoformat() if repo_stats.created_at else None,
        "updated_at": repo_stats.updated_at.isoformat() if repo_stats.updated_at else None,
        "pushed_at": repo_stats.pushed_at.isoformat() if repo_stats.pushed_at else None,
        "homepage": repo_stats.homepage,
        "has_releases": repo_stats.has_releases,
        "has_tags": repo_stats.has_tags,
        "languages": languages,
        "language_total_bytes": language_total_bytes,
    }


def _latest_repo_quality_snapshot(
    db: Session,
    owner: str,
    repo: str,
    include_report: bool = False,
) -> dict[str, object] | None:
    row = (
        db.query(
            ScanJob.id,
            ScanJob.commit_sha,
            ScanJob.finished_at,
            ScanReport.score_total,
            ScanReport.report_json,
        )
        .join(ScanReport, ScanReport.job_id == ScanJob.id)
        .filter(ScanJob.repo_owner == owner, ScanJob.repo_name == repo, ScanJob.status == "done")
        .order_by(ScanJob.finished_at.desc())
        .first()
    )
    if not row:
        return None

    payload: dict[str, object] = {}
    try:
        parsed = json.loads(row[4])
        if isinstance(parsed, dict):
            payload = parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        payload = {}

    project_metrics_raw = payload.get("project_metrics")
    project_metrics = project_metrics_raw if isinstance(project_metrics_raw, dict) else {}
    status_counts = {"pass": 0, "warn": 0, "fail": 0}
    category_scores: list[dict[str, object]] = []
    categories = payload.get("categories")
    if isinstance(categories, list):
        for category in categories:
            if not isinstance(category, dict):
                continue
            category_id = category.get("id")
            category_name = category.get("name")
            category_scores.append(
                {
                    "id": str(category_id) if category_id is not None else "unknown",
                    "name": str(category_name) if category_name is not None else "Unknown",
                    "score": int(category.get("score", 0) or 0),
                    "weight": int(category.get("weight", 0) or 0),
                }
            )
            checks = category.get("checks")
            if not isinstance(checks, list):
                continue
            for check in checks:
                if not isinstance(check, dict):
                    continue
                status = check.get("status")
                if isinstance(status, str) and status in status_counts:
                    status_counts[status] += 1

    detected_stacks = payload.get("detected_stacks")
    if not isinstance(detected_stacks, list):
        detected_stacks = []

    result: dict[str, object] = {
        "job_id": row[0],
        "commit_sha": row[1],
        "finished_at": row[2].isoformat() if row[2] else None,
        "score_total": int(row[3]),
        "report_url": f"/report/{row[0]}",
        "total_code_lines": int(project_metrics.get("total_code_lines", 0) or 0),
        "total_code_files": int(project_metrics.get("total_code_files", 0) or 0),
        "scanned_code_files": int(project_metrics.get("scanned_code_files", 0) or 0),
        "status_counts": status_counts,
        "category_scores": category_scores,
        "detected_stacks": [str(stack) for stack in detected_stacks[:20]],
    }
    if include_report:
        result["report"] = payload
    return result


def _parse_csv_flags(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _is_github_not_found_error(exc: GitHubAPIError) -> bool:
    return "GitHub API error (404)" in str(exc)


def _github_error_to_http(exc: GitHubAPIError) -> HTTPException:
    """Map GitHub API failures to clearer HTTP responses."""

    message = str(exc)
    lowered = message.lower()
    if "rate limit exceeded" in lowered:
        return HTTPException(
            status_code=429,
            detail=(
                "GitHub API rate limit exceeded. Add `github.token` to `config.yml` "
                "or set `RQI_GITHUB_TOKEN`, then restart the app."
            ),
        )
    if "(401)" in lowered or "bad credentials" in lowered:
        return HTTPException(
            status_code=401,
            detail="GitHub authentication failed. Check `github.token` in `config.yml`.",
        )
    if _is_github_not_found_error(exc):
        return HTTPException(status_code=404, detail="Repository not found.")
    return HTTPException(status_code=502, detail=message)


def _collect_custom_theme(raw_values: dict[str, str | None]) -> dict[str, str] | None:
    sanitized: dict[str, str] = {}
    for key in THEME_KEYS:
        value = raw_values.get(key)
        normalized = _normalize_hex_color(value)
        if normalized is not None:
            sanitized[key] = normalized
    return sanitized or None


def _normalize_hex_color(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not HEX_COLOR_RE.match(candidate):
        return None
    if len(candidate) == 4:
        candidate = "#" + "".join(char * 2 for char in candidate[1:])
    return candidate.upper()


def _select_dict_fields(data: dict[str, object], fields: str) -> dict[str, object]:
    allowed = _parse_csv_flags(fields)
    if not allowed:
        return data
    if "__none__" in allowed or "none" in allowed:
        return {}
    return {key: val for key, val in data.items() if key.lower() in allowed}


def _localize_quality_payload(payload: dict[str, object], lang: str) -> dict[str, object]:
    """Localize nested quality report fields for API consumers."""

    quality = payload.get("quality")
    if not isinstance(quality, dict):
        return payload

    report = quality.get("report")
    if isinstance(report, dict):
        localized_report = localize_report(report, lang)
        quality["report"] = localized_report
        categories = localized_report.get("categories")
        if isinstance(categories, list):
            name_by_id = {
                str(item.get("id")): str(item.get("name"))
                for item in categories
                if isinstance(item, dict) and item.get("id") and item.get("name")
            }
            category_scores = quality.get("category_scores")
            if isinstance(category_scores, list):
                for item in category_scores:
                    if not isinstance(item, dict):
                        continue
                    category_id = str(item.get("id", ""))
                    if category_id in name_by_id:
                        item["name"] = name_by_id[category_id]
    return payload


def _svg_cache_headers(cache_seconds: int) -> dict[str, str]:
    if cache_seconds <= 0:
        return {"Cache-Control": "no-store"}
    return {"Cache-Control": f"public, max-age={cache_seconds}"}


def _report_payload(db: Session, job_id: str) -> dict[str, object]:
    """Load and validate stored report payload for a completed job."""

    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "done" or not job.report:
        raise HTTPException(status_code=409, detail="Report is not ready")
    payload = json.loads(job.report.report_json)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Stored report is corrupted")
    return payload


def _mark_failed(job_id: str, error_message: str) -> None:
    """Mark scan job as failed and store error message."""

    db = SessionLocal()
    try:
        job = db.get(ScanJob, job_id)
        if not job:
            return
        job.status = "failed"
        job.progress = 100
        job.finished_at = datetime.now(UTC)
        job.error_message = error_message
        _metrics["scan_jobs_failed_total"] += 1
        db.commit()
    finally:
        db.close()


def _repo_history(db: Session, owner: str, repo: str, limit: int = 30) -> list[dict[str, object]]:
    rows = (
        db.query(ScanJob.id, ScanJob.created_at, ScanJob.commit_sha, ScanReport.score_total)
        .join(ScanReport, ScanReport.job_id == ScanJob.id)
        .filter(ScanJob.repo_owner == owner, ScanJob.repo_name == repo, ScanJob.status == "done")
        .order_by(ScanJob.created_at.desc())
        .limit(limit)
        .all()
    )
    history: list[dict[str, object]] = []
    prev_score: int | None = None
    for job_id, created_at, commit_sha, score in reversed(rows):
        delta = score - prev_score if prev_score is not None else 0
        history.append(
            {
                "job_id": job_id,
                "created_at": created_at.isoformat() if created_at else "",
                "score_total": score,
                "commit_sha": commit_sha,
                "commit_short": commit_sha[:7] if commit_sha else "n/a",
                "delta": delta,
            }
        )
        prev_score = int(score)
    return history


def _enforce_scan_access_limits(request: Request) -> None:
    """Apply per-client rate limit and daily quota."""

    identity = request.client.host if request.client else "unknown"
    now = time.time()
    queue = _scan_requests[identity]
    while queue and now - queue[0] > _RATE_WINDOW_SECONDS:
        queue.popleft()
    if len(queue) >= settings.scan_rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")
    queue.append(now)
    if settings.scan_daily_quota <= 0:
        return
    today = datetime.now(UTC).date()
    day, count = _scan_daily_usage.get(identity, (today, 0))
    if day != today:
        day, count = today, 0
    if count >= settings.scan_daily_quota:
        raise HTTPException(status_code=429, detail=f"Daily quota exceeded: {settings.scan_daily_quota}")
    _scan_daily_usage[identity] = (day, count + 1)


def _expire_stale_active_jobs(db: Session, owner: str, repo: str) -> None:
    cutoff = datetime.now(UTC) - timedelta(minutes=settings.stale_active_job_minutes)
    stale_jobs = (
        db.query(ScanJob)
        .filter(
            ScanJob.repo_owner == owner,
            ScanJob.repo_name == repo,
            ScanJob.status.in_(["queued", "running"]),
            ScanJob.created_at < cutoff,
        )
        .all()
    )
    if not stale_jobs:
        return
    now = datetime.now(UTC)
    for job in stale_jobs:
        job.status, job.progress, job.finished_at = "failed", 100, now
        job.error_message = "Marked as failed automatically because this scan job became stale."
    db.commit()


def _find_cached_report_for_commit(
    owner: str,
    repo: str,
    commit_sha: str | None,
    exclude_job_id: str,
) -> dict[str, object] | None:
    if not commit_sha or settings.scan_cache_ttl_seconds <= 0:
        return None
    db = SessionLocal()
    try:
        row = (
            db.query(ScanReport.score_total, ScanReport.report_json, ScanJob.finished_at)
            .join(ScanJob, ScanJob.id == ScanReport.job_id)
            .filter(
                ScanJob.repo_owner == owner,
                ScanJob.repo_name == repo,
                ScanJob.status == "done",
                ScanJob.commit_sha == commit_sha,
                ScanJob.id != exclude_job_id,
            )
            .order_by(ScanJob.finished_at.desc())
            .first()
        )
        if not row or row[2] is None:
            return None
        age_seconds = (datetime.now(UTC) - row[2].astimezone(UTC)).total_seconds()
        if age_seconds > settings.scan_cache_ttl_seconds:
            return None
        payload = json.loads(row[1])
        if isinstance(payload, dict):
            payload["score_total"] = int(row[0])
            return payload
        return None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    finally:
        db.close()


def _finalize_success_job(
    job_id: str,
    owner: str,
    repo: str,
    commit_sha: str | None,
    payload: dict[str, object],
) -> None:
    db = SessionLocal()
    try:
        job = db.get(ScanJob, job_id)
        if not job:
            return
        job.status, job.progress, job.finished_at, job.commit_sha = "done", 100, datetime.now(UTC), commit_sha
        report_row = db.get(ScanReport, job_id)
        report_json = json.dumps(payload)
        score = int(payload.get("score_total", 0))
        if report_row:
            report_row.score_total, report_row.report_json = score, report_json
        else:
            db.add(ScanReport(job_id=job_id, score_total=score, report_json=report_json))
        _cleanup_repo_jobs(db, owner, repo, job_id, commit_sha, settings.repo_history_keep)
        _metrics["scan_jobs_done_total"] += 1
        db.commit()
    finally:
        db.close()


def _latest_previous_report(owner: str, repo: str, exclude_job_id: str) -> dict[str, object] | None:
    db = SessionLocal()
    try:
        row = (
            db.query(ScanJob.id, ScanJob.commit_sha, ScanReport.report_json)
            .join(ScanReport, ScanReport.job_id == ScanJob.id)
            .filter(
                ScanJob.repo_owner == owner,
                ScanJob.repo_name == repo,
                ScanJob.status == "done",
                ScanJob.id != exclude_job_id,
            )
            .order_by(ScanJob.finished_at.desc())
            .first()
        )
        if not row:
            return None
        payload = json.loads(row[2])
        if not isinstance(payload, dict):
            return None
        return {"job_id": row[0], "commit_sha": row[1], "payload": payload}
    except (ValueError, TypeError, json.JSONDecodeError):
        return None
    finally:
        db.close()


def _extract_previous_score(previous: dict[str, object] | None) -> int | None:
    if not previous or not isinstance(previous.get("payload"), dict):
        return None
    try:
        return int(previous["payload"].get("score_total", 0))  # type: ignore[index]
    except (TypeError, ValueError):
        return None


def _build_report_comparison(
    previous: dict[str, object] | None,
    current_payload: dict[str, object],
    changed_files: list[str],
    current_commit_sha: str | None,
) -> ReportComparison:
    if not previous or not isinstance(previous.get("payload"), dict):
        return ReportComparison(
            previous_job_id=None,
            previous_commit_sha=None,
            current_commit_sha=current_commit_sha,
            score_delta=0,
            categories=[],
            checks=[],
            changed_files=changed_files[:100],
            changed_files_total=len(changed_files),
        )
    previous_payload = previous["payload"]  # type: ignore[index]
    prev_score = int(previous_payload.get("score_total", 0))
    cur_score = int(current_payload.get("score_total", 0))
    prev_cats = {c.get("id"): c for c in _as_list(previous_payload.get("categories")) if isinstance(c, dict)}
    cur_cats = {c.get("id"): c for c in _as_list(current_payload.get("categories")) if isinstance(c, dict)}

    category_deltas: list[CategoryDeltaItem] = []
    for cat_id, cur_cat in cur_cats.items():
        if not isinstance(cat_id, str):
            continue
        prev_cat = prev_cats.get(cat_id, {})
        cur_val = int(cur_cat.get("score", 0))
        prev_val = int(prev_cat.get("score", 0)) if isinstance(prev_cat, dict) else 0
        if cur_val != prev_val:
            category_deltas.append(
                CategoryDeltaItem(
                    category_id=cat_id,
                    category_name=str(cur_cat.get("name", cat_id)),
                    previous_score=prev_val,
                    current_score=cur_val,
                    delta=cur_val - prev_val,
                )
            )

    factors = {"pass": 1.0, "warn": 0.5, "fail": 0.0}
    prev_checks = _flatten_checks(prev_cats)
    cur_checks = _flatten_checks(cur_cats)
    check_deltas: list[CheckDeltaItem] = []
    for key, cur_entry in cur_checks.items():
        prev_entry = prev_checks.get(key)
        prev_status = prev_entry["status"] if prev_entry else None
        cur_status = cur_entry["status"]
        if prev_status == cur_status:
            continue
        weight = cur_entry["weight"]
        delta = round(weight * (factors[cur_status] - factors.get(prev_status, 0.0)), 2)
        check_deltas.append(
            CheckDeltaItem(
                category_id=cur_entry["category_id"],
                check_id=cur_entry["check_id"],
                check_name=cur_entry["check_name"],
                previous_status=prev_status,  # type: ignore[arg-type]
                current_status=cur_status,  # type: ignore[arg-type]
                score_delta=delta,
            )
        )
    check_deltas.sort(key=lambda item: abs(item.score_delta), reverse=True)

    return ReportComparison(
        previous_job_id=str(previous.get("job_id")) if previous.get("job_id") else None,
        previous_commit_sha=str(previous.get("commit_sha")) if previous.get("commit_sha") else None,
        current_commit_sha=current_commit_sha,
        score_delta=cur_score - prev_score,
        categories=category_deltas,
        checks=check_deltas[:50],
        changed_files=changed_files[:100],
        changed_files_total=len(changed_files),
    )


def _flatten_checks(categories: dict[object, object]) -> dict[str, dict[str, Any]]:
    flat: dict[str, dict[str, Any]] = {}
    for category_id, category in categories.items():
        if not isinstance(category_id, str) or not isinstance(category, dict):
            continue
        checks = _as_list(category.get("checks"))
        check_ids: list[str] = []
        for check in checks:
            if not isinstance(check, dict):
                continue
            check_id = check.get("id")
            if isinstance(check_id, str):
                check_ids.append(check_id)
        weight_map = check_weight_map(category_id, int(category.get("weight", 0)), check_ids)
        for check in checks:
            if not isinstance(check, dict):
                continue
            check_id = check.get("id")
            status = check.get("status")
            if not isinstance(check_id, str) or not isinstance(status, str):
                continue
            key = f"{category_id}:{check_id}"
            flat[key] = {
                "category_id": category_id,
                "check_id": check_id,
                "check_name": str(check.get("name", check_id)),
                "status": status,
                "weight": weight_map.get(check_id, 0.0),
            }
    return flat


def _as_list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _score_regression_check(
    previous_score: int | None,
    current_score: int,
    policy: RepoPolicy,
) -> CheckResult | None:
    if previous_score is None and policy.baseline_min_score is None:
        return None
    findings: list[tuple[str, str, str | None]] = []
    if policy.baseline_min_score is not None:
        if current_score < policy.baseline_min_score:
            findings.append(
                (
                    "fail",
                    f"Current score {current_score} is below baseline {policy.baseline_min_score}.",
                    "Improve checks to reach baseline score threshold.",
                )
            )
        else:
            findings.append(("pass", f"Current score {current_score} meets baseline threshold.", None))
    if previous_score is not None and policy.max_score_drop is not None:
        drop = previous_score - current_score
        if drop > policy.max_score_drop:
            findings.append(
                (
                    "fail",
                    (
                        "Score dropped by "
                        f"{drop} points versus previous scan ({previous_score} -> {current_score})."
                    ),
                    "Prevent regressions by fixing failing checks before merge.",
                )
            )
        elif drop > 0:
            findings.append(
                (
                    "warn",
                    (
                        "Score dropped by "
                        f"{drop} points versus previous scan ({previous_score} -> {current_score})."
                    ),
                    "Review changes that reduced quality score.",
                )
            )
        else:
            findings.append(("pass", "No score regression versus previous scan.", None))
    status = "pass"
    if any(item[0] == "fail" for item in findings):
        status = "fail"
    elif any(item[0] == "warn" for item in findings):
        status = "warn"
    return CheckResult(
        id="score_regression_guard",
        name="Score regression guard",
        status=status,  # type: ignore[arg-type]
        details="; ".join(item[1] for item in findings),
        recommendation=next((item[2] for item in findings if item[2]), None),
    )


def _cleanup_repo_jobs(
    db: Session,
    owner: str,
    repo: str,
    current_job_id: str,
    commit_sha: str | None,
    max_keep: int,
) -> None:
    """Prune outdated rows, keep latest and bounded history per repository."""

    jobs = (
        db.query(ScanJob)
        .filter(ScanJob.repo_owner == owner, ScanJob.repo_name == repo)
        .order_by(ScanJob.finished_at.desc(), ScanJob.created_at.desc())
        .all()
    )
    for job in jobs:
        job.is_latest = 1 if job.id == current_job_id else 0
    to_delete: set[str] = set()
    if commit_sha:
        to_delete.update(
            job.id
            for job in jobs
            if job.id != current_job_id and job.status == "done" and job.commit_sha == commit_sha
        )
    history_jobs = [
        j
        for j in jobs
        if j.status in {"done", "failed"} and j.id != current_job_id and j.id not in to_delete
    ]
    if max_keep > 0:
        to_delete.update(j.id for j in history_jobs[max(max_keep - 1, 0) :])
    for job in jobs:
        if job.id in to_delete:
            db.delete(job)


def _report_to_markdown(report: dict[str, object], lang: str = "en") -> str:
    """Serialize report payload to markdown/plain text export format."""

    ru = normalize_lang(lang) == "ru"
    if ru:
        labels = {
            "title": f"\u041e\u0442\u0447\u0435\u0442 {settings.app_name}",
            "repository": "\u0420\u0435\u043f\u043e\u0437\u0438\u0442\u043e\u0440\u0438\u0439",
            "total_score": (
                "\u0418\u0442\u043e\u0433\u043e\u0432\u0430\u044f "
                "\u043e\u0446\u0435\u043d\u043a\u0430"
            ),
            "generated_at": "\u0421\u0433\u0435\u043d\u0435\u0440\u0438\u0440\u043e\u0432\u0430\u043d\u043e",
            "comparison": "\u0421\u0440\u0430\u0432\u043d\u0435\u043d\u0438\u0435",
            "score_delta": (
                "\u0418\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0435 "
                "\u043e\u0446\u0435\u043d\u043a\u0438"
            ),
            "previous_commit": (
                "\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0438\u0439 "
                "\u043a\u043e\u043c\u043c\u0438\u0442"
            ),
            "current_commit": (
                "\u0422\u0435\u043a\u0443\u0449\u0438\u0439 "
                "\u043a\u043e\u043c\u043c\u0438\u0442"
            ),
            "unknown": "\u041d\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043d\u043e",
            "na": "\u043d/\u0434",
        }
        status_labels = {
            "pass": "\u041e\u041a",
            "warn": "\u041f\u0420\u0415\u0414",
            "fail": "\u041e\u0428\u0418\u0411",
        }
    else:
        labels = {
            "title": f"{settings.app_name} Report",
            "repository": "Repository",
            "total_score": "Total score",
            "generated_at": "Generated at",
            "comparison": "Comparison",
            "score_delta": "Score delta",
            "previous_commit": "Previous commit",
            "current_commit": "Current commit",
            "unknown": "Unknown",
            "na": "n/a",
        }
        status_labels = {
            "pass": "PASS",
            "warn": "WARN",
            "fail": "FAIL",
        }
    lines = [
        f"# {labels['title']}",
        "",
        f"- {labels['repository']}: {report.get('repo_url', '')}",
        f"- {labels['total_score']}: {report.get('score_total', 0)}/100",
        f"- {labels['generated_at']}: {report.get('generated_at', '')}",
        "",
    ]
    comparison = report.get("comparison")
    if isinstance(comparison, dict):
        lines.extend(
            [
                f"## {labels['comparison']}",
                f"- {labels['score_delta']}: {comparison.get('score_delta', 0)}",
                f"- {labels['previous_commit']}: {comparison.get('previous_commit_sha', labels['na'])}",
                f"- {labels['current_commit']}: {comparison.get('current_commit_sha', labels['na'])}",
                "",
            ]
        )
    for category in _as_list(report.get("categories")):
        if not isinstance(category, dict):
            continue
        lines.append(
            f"## {category.get('name', labels['unknown'])} "
            f"({category.get('score', 0)}/{category.get('weight', 0)})"
        )
        for check in _as_list(category.get("checks")):
            if not isinstance(check, dict):
                continue
            raw_status = str(check.get("status", "")).lower()
            status = status_labels.get(raw_status, raw_status.upper())
            lines.append(f"- [{status}] {check.get('name', '')}: {check.get('details', '')}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
