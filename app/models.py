"""SQLAlchemy models for scan jobs and generated reports."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ScanJob(Base):
    """Represents one scan execution request for a repository."""

    __tablename__ = "scan_jobs"
    __table_args__ = (
        Index("ix_scan_jobs_repo_status_created", "repo_owner", "repo_name", "status", "created_at"),
        Index("ix_scan_jobs_repo_finished", "repo_owner", "repo_name", "finished_at"),
        Index("ix_scan_jobs_repo_commit", "repo_owner", "repo_name", "commit_sha"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    repo_owner: Mapped[str] = mapped_column(String(255))
    repo_name: Mapped[str] = mapped_column(String(255))
    repo_url: Mapped[str] = mapped_column(String(512))
    commit_sha: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_latest: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    progress: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    report: Mapped["ScanReport | None"] = relationship(
        "ScanReport",
        back_populates="job",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ScanReport(Base):
    """Stores the computed report payload for a finished scan job."""

    __tablename__ = "scan_reports"

    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("scan_jobs.id"), primary_key=True)
    score_total: Mapped[int] = mapped_column(Integer)
    report_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    job: Mapped[ScanJob] = relationship("ScanJob", back_populates="report")
