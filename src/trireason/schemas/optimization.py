"""Pydantic schemas for the optimization API."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Request models ──────────────────────────────────────────────────


class OptimizationRequest(BaseModel):
    """User-submitted optimization job."""

    data: str = Field(..., description="Input data or context for prompt generation")
    objective: str = Field(..., description="Desired outcome the prompt should achieve")
    constraints: dict | None = Field(None, description="Optional constraints for generation")
    max_iterations: int = Field(5, ge=1, le=20, description="Maximum optimization iterations")
    score_threshold: int = Field(85, ge=0, le=100, description="Target score to stop early")


# ── Internal state passed between agents ────────────────────────────


class ScoreBreakdown(BaseModel):
    objective_fulfillment: float = Field(..., ge=0, le=100)
    correctness_faithfulness: float = Field(..., ge=0, le=100)
    completeness: float = Field(..., ge=0, le=100)
    format_compliance: float = Field(..., ge=0, le=100)
    clarity_usability: float = Field(..., ge=0, le=100)


class GeneratorOutput(BaseModel):
    candidate_prompt: str
    candidate_output: str


class CriticOutput(BaseModel):
    score_total: float = Field(..., ge=0, le=100)
    score_breakdown: ScoreBreakdown
    passed: bool
    issues: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class RefinerOutput(BaseModel):
    refined_prompt: str
    changes_made: list[str] = Field(default_factory=list)


# ── Response models ─────────────────────────────────────────────────


class IterationResponse(BaseModel):
    iteration_number: int
    candidate_prompt: str
    candidate_output: str
    score_total: float
    score_breakdown: ScoreBreakdown
    passed: bool
    issues: list[str]
    recommendations: list[str]
    is_best_so_far: bool


class OptimizationResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    total_iterations: int
    best_score: float | None
    best_prompt: str | None
    stop_reason: str | None
    iterations: list[IterationResponse]


class RunStatusResponse(BaseModel):
    run_id: uuid.UUID
    status: str
    total_iterations: int
    best_score: float | None
    stop_reason: str | None
    created_at: datetime
    updated_at: datetime


# ── SSE event models ────────────────────────────────────────────────


class IterationEvent(BaseModel):
    """Sent via SSE after each iteration completes."""

    event: str = "iteration"
    run_id: uuid.UUID
    iteration: IterationResponse


class CompletionEvent(BaseModel):
    """Sent via SSE when the optimization run finishes."""

    event: str = "complete"
    run_id: uuid.UUID
    best_score: float | None
    best_prompt: str | None
    stop_reason: str | None
    total_iterations: int
