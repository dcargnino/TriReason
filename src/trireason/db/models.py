"""SQLAlchemy models for TriReason iteration persistence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OptimizationRun(Base):
    """Top-level record for a full optimization session."""

    __tablename__ = "optimization_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    status: Mapped[str] = mapped_column(String(20), default="running")  # running | completed | failed
    user_data: Mapped[str] = mapped_column(Text)
    user_data_hash: Mapped[str] = mapped_column(String(64), index=True)
    objective: Mapped[str] = mapped_column(Text)
    constraints: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    max_iterations: Mapped[int] = mapped_column(Integer, default=5)
    score_threshold: Mapped[int] = mapped_column(Integer, default=85)
    best_iteration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    best_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    stop_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_iterations: Mapped[int] = mapped_column(Integer, default=0)


class Iteration(Base):
    """One iteration of the generate → critique → refine loop."""

    __tablename__ = "iterations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    iteration_number: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Generator outputs
    candidate_prompt: Mapped[str] = mapped_column(Text)
    candidate_output: Mapped[str] = mapped_column(Text)

    # Critic outputs
    score_total: Mapped[float] = mapped_column(Float)
    score_breakdown: Mapped[dict] = mapped_column(JSON)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    critic_issues: Mapped[list] = mapped_column(JSON, default=list)
    critic_recommendations: Mapped[list] = mapped_column(JSON, default=list)

    # Metadata
    is_best_so_far: Mapped[bool] = mapped_column(Boolean, default=False)
