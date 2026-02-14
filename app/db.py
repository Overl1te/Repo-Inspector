"""Database bootstrap and session utilities.

SQLite is the default backend for MVP, with compatibility migrations executed
at startup for incremental schema changes.
"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()


def _ensure_sqlite_directory(database_url: str) -> None:
    """Create parent directory for SQLite file when needed."""

    if not database_url.startswith("sqlite:///"):
        return
    raw_path = database_url.replace("sqlite:///", "", 1)
    if raw_path.startswith("./"):
        raw_path = raw_path[2:]
    db_file = Path(raw_path)
    if not db_file.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        db_file = project_root / db_file
    db_file.parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_directory(settings.database_url)

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for request lifecycle."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_compat_schema() -> None:
    """Apply idempotent compatibility migrations for SQLite deployments."""

    if not settings.database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        columns = {row[1] for row in conn.execute(text("PRAGMA table_info(scan_jobs)")).fetchall()}
        if "commit_sha" not in columns:
            conn.execute(text("ALTER TABLE scan_jobs ADD COLUMN commit_sha VARCHAR(64)"))
        if "is_latest" not in columns:
            conn.execute(text("ALTER TABLE scan_jobs ADD COLUMN is_latest INTEGER DEFAULT 0"))
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_scan_jobs_repo_status_created "
                "ON scan_jobs (repo_owner, repo_name, status, created_at)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_scan_jobs_repo_finished "
                "ON scan_jobs (repo_owner, repo_name, finished_at)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_scan_jobs_repo_commit "
                "ON scan_jobs (repo_owner, repo_name, commit_sha)"
            )
        )
