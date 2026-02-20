# Deployment Checklist

This document describes the minimum production-readiness checks before deploying Repo Inspector.

## 1. Environment

- Python `3.11+`
- Valid `config.yml` in project root
- Optional but recommended: GitHub token in `config.yml` (`github.token` or `github.app_token`)

## 2. Platform Config

- `vercel.json` contains routes for:
  - `/api`
  - `/api/(.*)`
  - `/health`
- GitHub Actions workflows in `.github/workflows/` define `timeout-minutes`.

## 3. Required Project Files

- `README.md`
- `README_EN.md`
- `CHANGELOG.md`
- `SUPPORT.md`
- `.editorconfig`

## 4. Pre-deploy Validation

Run the built-in validator:

```bash
python scripts/predeploy_check.py
```

Run strict mode (includes `ruff` and `pytest`):

```bash
python scripts/predeploy_check.py --strict
```

## 5. Deploy Targets

### Vercel (API)

- Entrypoint: `api/index.py`
- Config: `vercel.json`
- Smoke checks:
  - `GET /health`
  - `GET /api?owner=<owner>&repo=<repo>&kind=repo`

### GitHub Pages (Frontend)

- Static directory: `web/`
- Workflow: `.github/workflows/deploy-pages.yml`
- Ensure `web/config.js` points to your deployed API base URL.
