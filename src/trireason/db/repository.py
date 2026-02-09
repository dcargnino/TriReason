"""Database operations for optimization runs and iterations."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from trireason.db.models import Iteration, OptimizationRun


async def create_run(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    user_data: str,
    user_data_hash: str,
    objective: str,
    constraints: dict | None,
    max_iterations: int,
    score_threshold: int,
) -> OptimizationRun:
    """Insert a new optimization run."""
    run = OptimizationRun(
        id=run_id,
        user_data=user_data,
        user_data_hash=user_data_hash,
        objective=objective,
        constraints=constraints,
        max_iterations=max_iterations,
        score_threshold=score_threshold,
        status="running",
    )
    session.add(run)
    await session.flush()
    return run


async def save_iteration(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    iteration_number: int,
    candidate_prompt: str,
    candidate_output: str,
    score_total: float,
    score_breakdown: dict,
    passed: bool,
    critic_issues: list,
    critic_recommendations: list,
    is_best_so_far: bool,
) -> Iteration:
    """Insert a single iteration record."""
    it = Iteration(
        run_id=run_id,
        iteration_number=iteration_number,
        candidate_prompt=candidate_prompt,
        candidate_output=candidate_output,
        score_total=score_total,
        score_breakdown=score_breakdown,
        passed=passed,
        critic_issues=critic_issues,
        critic_recommendations=critic_recommendations,
        is_best_so_far=is_best_so_far,
    )
    session.add(it)
    await session.flush()
    return it


async def complete_run(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    best_iteration: int,
    best_score: float,
    best_prompt: str,
    stop_reason: str,
    total_iterations: int,
) -> None:
    """Mark a run as completed with final results."""
    await session.execute(
        update(OptimizationRun)
        .where(OptimizationRun.id == run_id)
        .values(
            status="completed",
            best_iteration=best_iteration,
            best_score=best_score,
            best_prompt=best_prompt,
            stop_reason=stop_reason,
            total_iterations=total_iterations,
        )
    )


async def fail_run(session: AsyncSession, *, run_id: uuid.UUID, reason: str) -> None:
    """Mark a run as failed."""
    await session.execute(
        update(OptimizationRun)
        .where(OptimizationRun.id == run_id)
        .values(status="failed", stop_reason=reason)
    )


async def get_run(session: AsyncSession, run_id: uuid.UUID) -> OptimizationRun | None:
    """Fetch a run by ID."""
    result = await session.execute(
        select(OptimizationRun).where(OptimizationRun.id == run_id)
    )
    return result.scalar_one_or_none()


async def get_iterations(session: AsyncSession, run_id: uuid.UUID) -> list[Iteration]:
    """Fetch all iterations for a run, ordered by iteration number."""
    result = await session.execute(
        select(Iteration)
        .where(Iteration.run_id == run_id)
        .order_by(Iteration.iteration_number)
    )
    return list(result.scalars().all())
