"""High-level optimization runner that coordinates workflow, persistence, and caching."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from trireason.cache.redis_cache import cache_prompt_pair, cache_run_result, get_cached_pair
from trireason.db import repository as repo
from trireason.schemas.optimization import (
    CompletionEvent,
    IterationEvent,
    IterationResponse,
    OptimizationResponse,
    ScoreBreakdown,
)
from trireason.utils.hashing import hash_text
from trireason.workflow.graph import build_graph, TriReasonState

logger = logging.getLogger(__name__)


async def run_and_persist(
    session: AsyncSession,
    *,
    data: str,
    objective: str,
    constraints: dict | None = None,
    max_iterations: int = 5,
    score_threshold: int = 85,
) -> OptimizationResponse:
    """Execute the optimization loop, persist every iteration, and return results."""
    run_id = uuid.uuid4()
    data_hash = hash_text(data)
    obj_hash = hash_text(objective)

    # Check cache for identical data+objective pair
    cached = await get_cached_pair(data_hash, obj_hash)
    if cached is not None:
        logger.info("Cache hit for data+objective pair")
        return OptimizationResponse(**cached)

    # Create the run record
    await repo.create_run(
        session,
        run_id=run_id,
        user_data=data,
        user_data_hash=data_hash,
        objective=objective,
        constraints=constraints,
        max_iterations=max_iterations,
        score_threshold=score_threshold,
    )
    await session.commit()

    try:
        graph = build_graph()
        initial_state: TriReasonState = {
            "run_id": str(run_id),
            "data": data,
            "objective": objective,
            "constraints": constraints,
            "max_iterations": max_iterations,
            "score_threshold": score_threshold,
            "iteration": 0,
            "candidate_prompt": "",
            "candidate_output": "",
            "critic_result": {},
            "best_score": 0.0,
            "best_prompt": "",
            "best_iteration": 0,
            "iterations_log": [],
            "stop_reason": None,
            "no_improvement_count": 0,
        }

        final_state = await graph.ainvoke(initial_state)

        # Persist iterations
        iterations_log: list[dict[str, Any]] = final_state.get("iterations_log", [])
        iteration_responses: list[IterationResponse] = []
        for it_data in iterations_log:
            breakdown = it_data["score_breakdown"]
            if isinstance(breakdown, dict):
                breakdown = ScoreBreakdown(**breakdown)
            await repo.save_iteration(
                session,
                run_id=run_id,
                iteration_number=it_data["iteration_number"],
                candidate_prompt=it_data["candidate_prompt"],
                candidate_output=it_data["candidate_output"],
                score_total=it_data["score_total"],
                score_breakdown=it_data["score_breakdown"] if isinstance(it_data["score_breakdown"], dict) else it_data["score_breakdown"].model_dump(),
                passed=it_data["passed"],
                critic_issues=it_data["issues"],
                critic_recommendations=it_data["recommendations"],
                is_best_so_far=it_data["is_best_so_far"],
            )
            iteration_responses.append(IterationResponse(**it_data))

        await repo.complete_run(
            session,
            run_id=run_id,
            best_iteration=final_state.get("best_iteration", 0),
            best_score=final_state.get("best_score", 0.0),
            best_prompt=final_state.get("best_prompt", ""),
            stop_reason=final_state.get("stop_reason", "unknown"),
            total_iterations=len(iterations_log),
        )
        await session.commit()

        response = OptimizationResponse(
            run_id=run_id,
            status="completed",
            total_iterations=len(iterations_log),
            best_score=final_state.get("best_score"),
            best_prompt=final_state.get("best_prompt"),
            stop_reason=final_state.get("stop_reason"),
            iterations=iteration_responses,
        )

        # Cache the result
        await cache_run_result(str(run_id), response.model_dump(mode="json"))
        await cache_prompt_pair(data_hash, obj_hash, response.model_dump(mode="json"))

        return response

    except Exception:
        await repo.fail_run(session, run_id=run_id, reason="internal_error")
        await session.commit()
        raise


async def run_streaming(
    session: AsyncSession,
    *,
    data: str,
    objective: str,
    constraints: dict | None = None,
    max_iterations: int = 5,
    score_threshold: int = 85,
) -> AsyncGenerator[IterationEvent | CompletionEvent, None]:
    """Execute optimization and yield SSE events after each iteration.

    This uses the LangGraph stream interface to emit events as they happen.
    """
    run_id = uuid.uuid4()
    data_hash = hash_text(data)

    await repo.create_run(
        session,
        run_id=run_id,
        user_data=data,
        user_data_hash=data_hash,
        objective=objective,
        constraints=constraints,
        max_iterations=max_iterations,
        score_threshold=score_threshold,
    )
    await session.commit()

    graph = build_graph()
    initial_state: TriReasonState = {
        "run_id": str(run_id),
        "data": data,
        "objective": objective,
        "constraints": constraints,
        "max_iterations": max_iterations,
        "score_threshold": score_threshold,
        "iteration": 0,
        "candidate_prompt": "",
        "candidate_output": "",
        "critic_result": {},
        "best_score": 0.0,
        "best_prompt": "",
        "best_iteration": 0,
        "iterations_log": [],
        "stop_reason": None,
        "no_improvement_count": 0,
    }

    last_state: dict[str, Any] = dict(initial_state)

    async for event in graph.astream(initial_state, stream_mode="updates"):
        # Each event is {node_name: state_update}
        for node_name, state_update in event.items():
            last_state.update(state_update)

            if node_name == "critique":
                iterations_log = last_state.get("iterations_log", [])
                if iterations_log:
                    latest = iterations_log[-1]
                    it_resp = IterationResponse(**latest)

                    await repo.save_iteration(
                        session,
                        run_id=run_id,
                        iteration_number=latest["iteration_number"],
                        candidate_prompt=latest["candidate_prompt"],
                        candidate_output=latest["candidate_output"],
                        score_total=latest["score_total"],
                        score_breakdown=latest["score_breakdown"] if isinstance(latest["score_breakdown"], dict) else latest["score_breakdown"].model_dump(),
                        passed=latest["passed"],
                        critic_issues=latest["issues"],
                        critic_recommendations=latest["recommendations"],
                        is_best_so_far=latest["is_best_so_far"],
                    )
                    await session.commit()

                    yield IterationEvent(run_id=run_id, iteration=it_resp)

    # Finalize
    await repo.complete_run(
        session,
        run_id=run_id,
        best_iteration=last_state.get("best_iteration", 0),
        best_score=last_state.get("best_score", 0.0),
        best_prompt=last_state.get("best_prompt", ""),
        stop_reason=last_state.get("stop_reason", "unknown"),
        total_iterations=last_state.get("iteration", 0),
    )
    await session.commit()

    yield CompletionEvent(
        run_id=run_id,
        best_score=last_state.get("best_score"),
        best_prompt=last_state.get("best_prompt"),
        stop_reason=last_state.get("stop_reason"),
        total_iterations=last_state.get("iteration", 0),
    )
