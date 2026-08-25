from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Defect(Base):
    __tablename__ = "defects"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_issue_number: Mapped[int] = mapped_column(Integer, unique=True)
    slug: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="open")  # open|in_review|merged|retesting|closed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    pull_requests: Mapped[list["PullRequest"]] = relationship(back_populates="defect")
    test_runs: Mapped[list["TestRun"]] = relationship(back_populates="defect")


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    github_pr_number: Mapped[int] = mapped_column(Integer, unique=True)
    defect_id: Mapped[int | None] = mapped_column(ForeignKey("defects.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open")  # open|approved|changes_requested|merged
    review_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    defect: Mapped["Defect | None"] = relationship(back_populates="pull_requests")
    review_results: Mapped[list["ReviewResult"]] = relationship(back_populates="pull_request")


class ReviewResult(Base):
    __tablename__ = "review_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(ForeignKey("pull_requests.id"))
    verdict: Mapped[str] = mapped_column(String(32))  # approve|request_changes
    comments: Mapped[str] = mapped_column(Text, default="")
    model_used: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    pull_request: Mapped["PullRequest"] = relationship(back_populates="review_results")


class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    defect_id: Mapped[int] = mapped_column(ForeignKey("defects.id"))
    pull_request_id: Mapped[int | None] = mapped_column(ForeignKey("pull_requests.id"), nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    report: Mapped[str] = mapped_column(Text, default="")
    ai_summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    defect: Mapped["Defect"] = relationship(back_populates="test_runs")
