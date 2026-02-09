"""LangGraph workflow for the TriReason optimization loop.

State machine:
  generate → critique → (pass? → end | fail? → refine → generate → ...)
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from trireason.agents.critic import critique
from trireason.agents.generator import generate_from_refinement, generate_initial
from trireason.agents.refiner import refine
from trireason.schemas.optimization import CriticOutput, GeneratorOutput, IterationResponse, ScoreBreakdown

logger = logging.getLogger(__name__)


# ── Workflow state ──────────────────────────────────────────────────


class TriReasonState(TypedDict, total=False):
    # Inputs (set once)
    run_id: str
    data: str
    objective: str
    constraints: dict | None
    max_iterations: int
    score_threshold: int

    # Mutable across iterations
    iteration: int
    candidate_prompt: str
    candidate_output: str
    critic_result: dict[str, Any]
    best_score: float
    best_prompt: str
    best_iteration: int
    iterations_log: list[dict[str, Any]]
    stop_reason: str | None
    no_improvement_count: int


# ── Node functions ──────────────────────────────────────────────────


async def generate_node(state: TriReasonState) -> dict[str, Any]:
    """Run the Generator agent."""
    iteration = state.get("iteration", 0) + 1
    logger.info("Iteration %d – generating prompt", iteration)

    if iteration == 1:
        result: GeneratorOutput = await generate_initial(
            data=state["data"],
            objective=state["objective"],
            constraints=state.get("constraints"),
        )
    else:
        critic: dict[str, Any] = state["critic_result"]
        result = await generate_from_refinement(
            data=state["data"],
            objective=state["objective"],
            refined_prompt=state["candidate_prompt"],
            critic_issues=critic.get("issues", []),
            constraints=state.get("constraints"),
        )

    return {
        "iteration": iteration,
        "candidate_prompt": result.candidate_prompt,
        "candidate_output": result.candidate_output,
    }


async def critique_node(state: TriReasonState) -> dict[str, Any]:
    """Run the Critic agent and update best-tracking."""
    logger.info("Iteration %d – critiquing output", state["iteration"])

    result: CriticOutput = await critique(
        data=state["data"],
        objective=state["objective"],
        candidate_prompt=state["candidate_prompt"],
        candidate_output=state["candidate_output"],
        threshold=state["score_threshold"],
    )

    best_score = state.get("best_score", 0.0)
    best_prompt = state.get("best_prompt", state["candidate_prompt"])
    best_iteration = state.get("best_iteration", state["iteration"])
    no_improvement_count = state.get("no_improvement_count", 0)
    is_best = result.score_total > best_score

    if is_best:
        best_score = result.score_total
        best_prompt = state["candidate_prompt"]
        best_iteration = state["iteration"]
        no_improvement_count = 0
    else:
        no_improvement_count += 1

    iteration_record = IterationResponse(
        iteration_number=state["iteration"],
        candidate_prompt=state["candidate_prompt"],
        candidate_output=state["candidate_output"],
        score_total=result.score_total,
        score_breakdown=result.score_breakdown,
        passed=result.passed,
        issues=result.issues,
        recommendations=result.recommendations,
        is_best_so_far=is_best,
    )

    iterations_log = list(state.get("iterations_log", []))
    iterations_log.append(iteration_record.model_dump())

    # Determine stop reason
    stop_reason: str | None = None
    if result.passed:
        stop_reason = "threshold_reached"
    elif state["iteration"] >= state["max_iterations"]:
        stop_reason = "max_iterations_reached"
    elif no_improvement_count >= 3:
        stop_reason = "no_improvement"

    return {
        "critic_result": result.model_dump(),
        "best_score": best_score,
        "best_prompt": best_prompt,
        "best_iteration": best_iteration,
        "iterations_log": iterations_log,
        "stop_reason": stop_reason,
        "no_improvement_count": no_improvement_count,
    }


async def refine_node(state: TriReasonState) -> dict[str, Any]:
    """Run the Refiner agent."""
    logger.info("Iteration %d – refining prompt", state["iteration"])
    critic: dict[str, Any] = state["critic_result"]

    result = await refine(
        current_prompt=state["candidate_prompt"],
        objective=state["objective"],
        issues=critic.get("issues", []),
        recommendations=critic.get("recommendations", []),
        score_total=critic.get("score_total", 0),
    )

    return {
        "candidate_prompt": result.refined_prompt,
    }


# ── Conditional edge ───────────────────────────────────────────────


def should_continue(state: TriReasonState) -> str:
    """Decide whether to refine or stop."""
    if state.get("stop_reason") is not None:
        return "end"
    return "refine"


# ── Build the graph ────────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Construct and compile the TriReason optimization graph."""
    graph = StateGraph(TriReasonState)

    graph.add_node("generate", generate_node)
    graph.add_node("critique", critique_node)
    graph.add_node("refine", refine_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "critique")
    graph.add_conditional_edges("critique", should_continue, {"refine": "refine", "end": END})
    graph.add_edge("refine", "generate")

    return graph.compile()


# ── Public runner ──────────────────────────────────────────────────


async def run_optimization(
    data: str,
    objective: str,
    constraints: dict | None = None,
    max_iterations: int = 5,
    score_threshold: int = 85,
    run_id: str | None = None,
) -> TriReasonState:
    """Execute the full optimization loop and return final state."""
    graph = build_graph()

    initial_state: TriReasonState = {
        "run_id": run_id or str(uuid.uuid4()),
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
    return final_state
