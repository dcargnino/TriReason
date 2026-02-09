"""API routes for the TriReason optimization service."""

from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from trireason.cache.redis_cache import get_cached_run
from trireason.db import repository as repo
from trireason.db.session import get_db
from trireason.schemas.optimization import (
    CompletionEvent,
    IterationEvent,
    IterationResponse,
    OptimizationRequest,
    OptimizationResponse,
    RunStatusResponse,
    ScoreBreakdown,
)
from trireason.workflow.runner import run_and_persist, run_streaming

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["optimization"])


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize(
    request: OptimizationRequest,
    session: AsyncSession = Depends(get_db),
) -> OptimizationResponse:
    """Run a synchronous optimization and return the full result."""
    result = await run_and_persist(
        session,
        data=request.data,
        objective=request.objective,
        constraints=request.constraints,
        max_iterations=request.max_iterations,
        score_threshold=request.score_threshold,
    )
    return result


@router.post("/optimize/stream")
async def optimize_stream(
    request: OptimizationRequest,
    session: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """Run optimization with real-time SSE streaming of iteration results."""

    async def event_generator():
        async for event in run_streaming(
            session,
            data=request.data,
            objective=request.objective,
            constraints=request.constraints,
            max_iterations=request.max_iterations,
            score_threshold=request.score_threshold,
        ):
            if isinstance(event, IterationEvent):
                yield {
                    "event": "iteration",
                    "data": event.model_dump_json(),
                }
            elif isinstance(event, CompletionEvent):
                yield {
                    "event": "complete",
                    "data": event.model_dump_json(),
                }

    return EventSourceResponse(event_generator())


@router.get("/runs/{run_id}", response_model=OptimizationResponse)
async def get_run(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> OptimizationResponse:
    """Retrieve a completed optimization run by ID."""
    # Try cache first
    cached = await get_cached_run(str(run_id))
    if cached is not None:
        return OptimizationResponse(**cached)

    run = await repo.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    iterations = await repo.get_iterations(session, run_id)
    iteration_responses = [
        IterationResponse(
            iteration_number=it.iteration_number,
            candidate_prompt=it.candidate_prompt,
            candidate_output=it.candidate_output,
            score_total=it.score_total,
            score_breakdown=ScoreBreakdown(**it.score_breakdown),
            passed=it.passed,
            issues=it.critic_issues,
            recommendations=it.critic_recommendations,
            is_best_so_far=it.is_best_so_far,
        )
        for it in iterations
    ]

    return OptimizationResponse(
        run_id=run.id,
        status=run.status,
        total_iterations=run.total_iterations,
        best_score=run.best_score,
        best_prompt=run.best_prompt,
        stop_reason=run.stop_reason,
        iterations=iteration_responses,
    )


@router.get("/runs/{run_id}/status", response_model=RunStatusResponse)
async def get_run_status(
    run_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> RunStatusResponse:
    """Check the status of an optimization run."""
    run = await repo.get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    return RunStatusResponse(
        run_id=run.id,
        status=run.status,
        total_iterations=run.total_iterations,
        best_score=run.best_score,
        stop_reason=run.stop_reason,
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.get("/health")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": "trireason"}
