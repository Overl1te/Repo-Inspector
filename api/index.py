"""Vercel ASGI entrypoint.

This file enables deploying FastAPI app as a serverless endpoint.
"""

from __future__ import annotations

import os

# Use writable ephemeral storage on Vercel for SQLite if user did not override DB URL.
if os.getenv("VERCEL") and not os.getenv("RQI_DATABASE_URL"):
    os.environ["RQI_DATABASE_URL"] = "sqlite:////tmp/repo_inspector.db"

from app.main import app as app  # noqa: F401
