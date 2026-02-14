# Project Structure

## Top-level layout

```text
Repo-Inspector/
├── app/                      # FastAPI app, scanner logic, templates, static assets
│   ├── main.py               # API routes, background job lifecycle, stats endpoints
│   ├── github_client.py      # Async GitHub REST client
│   ├── scanner/              # Checks, scoring, schemas, policy parser, i18n
│   ├── templates/            # Jinja2 HTML templates + SVG XML templates
│   ├── static/               # CSS/JS/logo assets for UI
│   ├── themes/               # Dynamic theme JSON configs for SVG generator
│   └── locales/              # Translation catalog (`translations.json`)
├── scripts/                  # CLI scripts for report generation/PR summaries
├── tests/                    # Unit tests
├── web/                      # Static Pages mode frontend and generated reports
├── data/                     # SQLite database (runtime)
├── config.yml                # Public runtime config
├── Dockerfile                # Container image
├── docker-compose.yml        # Local compose stack
├── pyproject.toml            # Build metadata + ruff/pytest config
├── requirements.txt          # Runtime dependencies
└── run.bat                   # Windows quick-start runner
```

## Runtime flow

1. Client calls `POST /api/scan` with GitHub URL (+ optional one-time token).
2. API creates `ScanJob` row with `queued` status.
3. Background task runs async scanner (`GitHubClient` + checks + scoring).
4. Result stored in `ScanReport`, status becomes `done` or `failed`.
5. UI polls `GET /api/jobs/{job_id}` until completion.

## Deployment checklist

- `config.yml` exists and has correct `database.url`/`github.token` values.
- `data/` directory is writable by app process.
- `ruff check .` and `pytest -q` are green.
- Governance docs are present (`CODE_OF_CONDUCT`, `CONTRIBUTING`, `SECURITY`, `TERMS_OF_USE`, `CITATION`).
- Health endpoint returns 200: `GET /health`.
