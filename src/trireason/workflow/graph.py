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
            iteration=iteration,
        )
    else:
        critic: dict[str, Any] = state["critic_result"]
        result = await generate_from_refinement(
            data=state["data"],
            objective=state["objective"],
            refined_prompt=state["candidate_prompt"],
            critic_issues=critic.get("issues", []),
            constraints=state.get("constraints"),
            iteration=iteration,
        )

    return {
        "iteration": iteration,
        "candidate_prompt": result.candidate_prompt,
        "candidate_output": result.candidate_output,
    }


async def critique_node(state: TriReasonState) -> dict[str, Any]:
    """Run the Critic agent and update best-tracking."""
    iteration = state.get("iteration", 1)
    logger.info("Iteration %d – critiquing output", iteration)

    result: CriticOutput = await critique(
        data=state["data"],
        objective=state["objective"],
        candidate_output=state["candidate_output"],
        iteration=iteration,
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

    score_threshold = state.get("score_threshold", 85)
    passed = result.score_total >= score_threshold

    iteration_record = IterationResponse(
        iteration_number=state["iteration"],
        candidate_prompt=state["candidate_prompt"],
        candidate_output=state["candidate_output"],
        score_total=result.score_total,
        score_breakdown=result.score_breakdown,
        passed=passed,
        issues=result.issues,
        recommendations=result.recommendations,
        is_best_so_far=is_best,
    )

    iterations_log = list(state.get("iterations_log", []))
    iterations_log.append(iteration_record.model_dump())

    return {
        "critic_result": result.model_dump(),
        "best_score": best_score,
        "best_prompt": best_prompt,
        "best_iteration": best_iteration,
        "iterations_log": iterations_log,
        "no_improvement_count": no_improvement_count,
    }


async def refine_node(state: TriReasonState) -> dict[str, Any]:
    """Run the Refiner agent and decide whether to continue or stop."""
    iteration = state.get("iteration", 1)
    logger.info("Iteration %d – refining prompt", iteration)
    critic: dict[str, Any] = state["critic_result"]

    result = await refine(
        current_system_message=state["candidate_prompt"],
        objective=state["objective"],
        data=state["data"],
        critic_feedback=critic,
        quality_threshold=state.get("score_threshold", 85),
        iteration=iteration,
    )

    # Refiner decides action
    action = result.action
    stop_reason: str | None = None
    
    if action == "stop":
        stop_reason = result.reason
    elif state.get("iteration", 0) >= state.get("max_iterations", 5):
        stop_reason = "max_iterations_reached"

    # Update the last iteration in the log with refiner info
    iterations_log = list(state.get("iterations_log", []))
    if iterations_log:
        last = iterations_log[-1]
        last["refiner_action"] = action
        last["refiner_reason"] = result.reason
        last["changes_made"] = result.changes_made

    return {
        "candidate_prompt": result.refined_prompt,
        "stop_reason": stop_reason,
        "iterations_log": iterations_log,
    }


# ── Conditional edge ───────────────────────────────────────────────


def should_continue(state: TriReasonState) -> str:
    """Decide whether to generate again or stop based on Refiner's decision."""
    if state.get("stop_reason") is not None:
        return "end"
    return "generate"


# ── Build the graph ────────────────────────────────────────────────


def build_graph() -> StateGraph:
    """Construct and compile the TriReason optimization graph."""
    graph = StateGraph(TriReasonState)

    graph.add_node("generate", generate_node)
    graph.add_node("critique", critique_node)
    graph.add_node("refine", refine_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "critique")
    graph.add_edge("critique", "refine")
    graph.add_conditional_edges("refine", should_continue, {"generate": "generate", "end": END})

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
