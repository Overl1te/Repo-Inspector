# Contributing to Repo Inspector

<p align="left">
  <a href="CONTRIBUTING.md">Русская версия</a> •
  <a href="README.md">README</a> •
  <a href="CODE_OF_CONDUCT_EN.md">Code of Conduct</a> •
  <a href="SECURITY_EN.md">Security</a>
</p>

This guide explains how to contribute changes while keeping the project
stable, secure, and deployment-ready.

## Principles

- Keep changes small, atomic, and reviewable.
- Security and correctness over quick hacks.
- Update docs when behavior changes.
- If behavior changes, tests should reflect it.

## Stack

- Python 3.11+
- FastAPI + Uvicorn
- httpx (async)
- SQLAlchemy 2.0 + SQLite
- Jinja2 + vanilla JS
- pytest + ruff

## Project map

See `docs/PROJECT_STRUCTURE.md`.

## Workflow

1. Branch from `main`.
2. Implement a minimal coherent change set.
3. Add/update tests.
4. Update relevant docs.
5. Open a PR with clear motivation and impact.

Recommended branch names:

- `feat/<short-name>`
- `fix/<short-name>`
- `refactor/<short-name>`
- `docs/<short-name>`
- `chore/<short-name>`

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .[dev]
uvicorn app.main:app --reload
```

## Pre-PR checks

```bash
ruff check .
pytest -q
```

## Coding standards

- Use explicit typing for public/API-facing functions.
- Add docstrings where intent is not obvious.
- Use comments for rationale and constraints, not syntax narration.
- Avoid dead/commented-out code.
- Minimize hidden side effects and mutable globals.

## Security policy

- Never commit secrets or tokens.
- Security fixes should include tests or reproducible validation.
- Report vulnerabilities via `SECURITY_EN.md`, not public issues.

## PR checklist

- [ ] Change addresses a specific problem.
- [ ] Tests added/updated, or rationale provided.
- [ ] README/docs updated if behavior changed.
- [ ] `ruff` and `pytest` passed locally.
- [ ] No secrets, debug leftovers, or temp artifacts.

## Need help?

Open an issue: <https://github.com/Overl1te/Repo-Inspector/issues>
