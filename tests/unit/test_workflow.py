"""Tests for the LangGraph workflow."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from trireason.workflow.graph import build_graph, run_optimization, should_continue


class TestConditionalEdge:
    def test_should_stop_on_threshold(self):
        state = {"stop_reason": "threshold_reached"}
        assert should_continue(state) == "end"

    def test_should_stop_on_max_iterations(self):
        state = {"stop_reason": "max_iterations_reached"}
        assert should_continue(state) == "end"

    def test_should_stop_on_no_improvement(self):
        state = {"stop_reason": "no_improvement"}
        assert should_continue(state) == "end"

    def test_should_continue(self):
        state = {"stop_reason": None}
        assert should_continue(state) == "refine"

    def test_should_continue_no_key(self):
        state = {}
        assert should_continue(state) == "refine"


class TestBuildGraph:
    def test_graph_compiles(self):
        graph = build_graph()
        assert graph is not None


class TestRunOptimization:
    @pytest.mark.asyncio
    async def test_single_iteration_pass(self):
        """Test that the workflow stops after one iteration if the score passes."""
        gen_response = json.dumps({
            "candidate_prompt": "Test prompt",
            "candidate_output": "Test output",
        })
        critic_response = json.dumps({
            "score_total": 92.0,
            "score_breakdown": {
                "objective_fulfillment": 95,
                "correctness_faithfulness": 90,
                "completeness": 88,
                "format_compliance": 92,
                "clarity_usability": 90,
            },
            "passed": True,
            "issues": [],
            "recommendations": [],
        })

        with patch("trireason.agents.generator.chat_json", new_callable=AsyncMock) as mock_gen, \
             patch("trireason.agents.critic.chat_json", new_callable=AsyncMock) as mock_crit:
            mock_gen.return_value = gen_response
            mock_crit.return_value = critic_response

            state = await run_optimization(
                data="test data",
                objective="test objective",
                max_iterations=5,
                score_threshold=85,
            )

            assert state["stop_reason"] == "threshold_reached"
            assert state["best_score"] == 92.0
            assert len(state["iterations_log"]) == 1
            assert mock_gen.call_count == 1
            assert mock_crit.call_count == 1

    @pytest.mark.asyncio
    async def test_multiple_iterations_then_pass(self):
        """Test that the workflow iterates and stops when threshold is reached."""
        gen_response = json.dumps({
            "candidate_prompt": "Test prompt",
            "candidate_output": "Test output",
        })
        fail_critic = json.dumps({
            "score_total": 70.0,
            "score_breakdown": {
                "objective_fulfillment": 70,
                "correctness_faithfulness": 70,
                "completeness": 70,
                "format_compliance": 70,
                "clarity_usability": 70,
            },
            "passed": False,
            "issues": ["Needs improvement"],
            "recommendations": ["Improve X"],
        })
        pass_critic = json.dumps({
            "score_total": 90.0,
            "score_breakdown": {
                "objective_fulfillment": 92,
                "correctness_faithfulness": 88,
                "completeness": 85,
                "format_compliance": 95,
                "clarity_usability": 90,
            },
            "passed": True,
            "issues": [],
            "recommendations": [],
        })
        refine_response = json.dumps({
            "refined_prompt": "Improved prompt",
            "changes_made": ["Changed X"],
        })

        with patch("trireason.agents.generator.chat_json", new_callable=AsyncMock) as mock_gen, \
             patch("trireason.agents.critic.chat_json", new_callable=AsyncMock) as mock_crit, \
             patch("trireason.agents.refiner.chat_json", new_callable=AsyncMock) as mock_ref:
            mock_gen.return_value = gen_response
            mock_crit.side_effect = [fail_critic, pass_critic]
            mock_ref.return_value = refine_response

            state = await run_optimization(
                data="test data",
                objective="test objective",
                max_iterations=5,
                score_threshold=85,
            )

            assert state["stop_reason"] == "threshold_reached"
            assert state["best_score"] == 90.0
            assert len(state["iterations_log"]) == 2

    @pytest.mark.asyncio
    async def test_max_iterations_reached(self):
        """Test that the workflow stops at max iterations."""
        gen_response = json.dumps({
            "candidate_prompt": "Test prompt",
            "candidate_output": "Test output",
        })
        fail_critic = json.dumps({
            "score_total": 60.0,
            "score_breakdown": {
                "objective_fulfillment": 60,
                "correctness_faithfulness": 60,
                "completeness": 60,
                "format_compliance": 60,
                "clarity_usability": 60,
            },
            "passed": False,
            "issues": ["Still needs work"],
            "recommendations": ["Keep improving"],
        })
        refine_response = json.dumps({
            "refined_prompt": "Slightly improved prompt",
            "changes_made": ["Minor change"],
        })

        # Critic scores increase slightly each time to avoid no_improvement stop
        critic_responses = []
        for i in range(2):
            score = 60 + i * 5
            critic_responses.append(json.dumps({
                "score_total": score,
                "score_breakdown": {
                    "objective_fulfillment": score,
                    "correctness_faithfulness": score,
                    "completeness": score,
                    "format_compliance": score,
                    "clarity_usability": score,
                },
                "passed": False,
                "issues": ["Needs more"],
                "recommendations": ["Do more"],
            }))

        with patch("trireason.agents.generator.chat_json", new_callable=AsyncMock) as mock_gen, \
             patch("trireason.agents.critic.chat_json", new_callable=AsyncMock) as mock_crit, \
             patch("trireason.agents.refiner.chat_json", new_callable=AsyncMock) as mock_ref:
            mock_gen.return_value = gen_response
            mock_crit.side_effect = critic_responses
            mock_ref.return_value = refine_response

            state = await run_optimization(
                data="test data",
                objective="test objective",
                max_iterations=2,
                score_threshold=85,
            )

            assert state["stop_reason"] == "max_iterations_reached"
            assert len(state["iterations_log"]) == 2
