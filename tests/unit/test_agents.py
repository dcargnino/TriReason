"""Tests for agent modules using mocked LLM calls."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from trireason.agents.critic import critique
from trireason.agents.generator import generate_from_refinement, generate_initial
from trireason.agents.refiner import refine


@pytest.fixture
def mock_generator_response():
    return json.dumps({
        "candidate_prompt": "You are a data analyst. Summarize the following sales data.",
        "candidate_output": "Sales grew 25% in Q1 2025.",
    })


@pytest.fixture
def mock_generator_response_refine():
    return json.dumps({
        "candidate_prompt": "You are a senior data analyst with trend analysis focus.",
        "candidate_output": "Sales showed strong upward trend with 25% growth in Q1 2025.",
    })


@pytest.fixture
def mock_critic_response():
    return json.dumps({
        "score_total": 82.0,
        "score_breakdown": {
            "objective_fulfillment": 85,
            "correctness_faithfulness": 80,
            "completeness": 75,
            "format_compliance": 90,
            "clarity_usability": 85,
        },
        "passed": False,
        "issues": ["Missing trend analysis"],
        "recommendations": ["Add month-over-month comparison"],
    })


@pytest.fixture
def mock_critic_response_passing():
    return json.dumps({
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


@pytest.fixture
def mock_refiner_response_continue():
    return json.dumps({
        "refined_prompt": "You are a senior data analyst. Provide a detailed summary with trend analysis.",
        "action": "continue",
        "reason": "Score below threshold, further refinement needed",
        "changes_made": ["Added trend analysis requirement"],
    })


@pytest.fixture
def mock_refiner_response_stop():
    return json.dumps({
        "refined_prompt": "You are an expert data analyst with comprehensive analysis capabilities.",
        "action": "stop",
        "reason": "no_improvement",
        "changes_made": ["Minor formatting adjustment"],
    })


class TestGenerator:
    @pytest.mark.asyncio
    async def test_generate_initial_basic(self, mock_generator_response):
        with patch("trireason.agents.generator.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response

            result = await generate_initial(
                data="Sales: Jan=$100k, Feb=$110k",
                objective="Summarize sales trends",
            )

            assert result.candidate_prompt is not None
            assert result.candidate_output is not None
            assert len(result.candidate_prompt) > 0
            assert len(result.candidate_output) > 0
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_initial_with_constraints(self, mock_generator_response):
        with patch("trireason.agents.generator.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response

            result = await generate_initial(
                data="Sales data",
                objective="Create summary",
                constraints={"format": "bullet points", "max_length": 100},
            )

            assert result.candidate_prompt is not None
            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "CONSTRAINTS" in user_msg or "constraints" in user_msg.lower()

    @pytest.mark.asyncio
    async def test_generate_initial_includes_data_and_objective(self, mock_generator_response):
        with patch("trireason.agents.generator.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response

            await generate_initial(
                data="Specific sales data",
                objective="Specific objective",
            )

            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "Specific sales data" in user_msg
            assert "Specific objective" in user_msg

    @pytest.mark.asyncio
    async def test_generate_from_refinement_basic(self, mock_generator_response_refine):
        with patch("trireason.agents.generator.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response_refine

            result = await generate_from_refinement(
                data="data",
                objective="objective",
                refined_prompt="improved prompt",
                critic_issues=["issue1"],
            )

            assert result.candidate_prompt is not None
            assert result.candidate_output is not None
            assert "trend" in result.candidate_output.lower()

    @pytest.mark.asyncio
    async def test_generate_from_refinement_includes_feedback(self, mock_generator_response_refine):
        with patch("trireason.agents.generator.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response_refine

            await generate_from_refinement(
                data="sales data",
                objective="analyze trends",
                refined_prompt="refined prompt",
                critic_issues=["Missing analysis", "Poor formatting"],
            )

            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "Missing analysis" in user_msg or "critic" in user_msg.lower()

    @pytest.mark.asyncio
    async def test_generate_from_refinement_with_constraints(self, mock_generator_response_refine):
        with patch("trireason.agents.generator.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response_refine

            await generate_from_refinement(
                data="data",
                objective="objective",
                refined_prompt="prompt",
                critic_issues=["issue"],
                constraints={"format": "table"},
            )

            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "table" in user_msg.lower()


class TestCritic:
    @pytest.mark.asyncio
    async def test_critique_failing(self, mock_critic_response):
        with patch("trireason.agents.critic.critic.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_critic_response

            result = await critique(
                data="data",
                objective="objective",
                candidate_output="output",
            )

            assert result.score_total == 82.0
            assert len(result.issues) == 1
            assert result.issues[0] == "Missing trend analysis"
            assert len(result.recommendations) == 1

    @pytest.mark.asyncio
    async def test_critique_passing(self, mock_critic_response_passing):
        with patch("trireason.agents.critic.critic.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_critic_response_passing

            result = await critique(
                data="data",
                objective="objective",
                candidate_output="output",
            )

            assert result.score_total == 92.0
            assert len(result.issues) == 0
            assert len(result.recommendations) == 0

    @pytest.mark.asyncio
    async def test_critique_score_breakdown_structure(self, mock_critic_response):
        with patch("trireason.agents.critic.critic.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_critic_response

            result = await critique(
                data="data",
                objective="objective",
                candidate_output="output",
            )

            assert result.score_breakdown.objective_fulfillment == 85
            assert result.score_breakdown.correctness_faithfulness == 80
            assert result.score_breakdown.completeness == 75
            assert result.score_breakdown.format_compliance == 90
            assert result.score_breakdown.clarity_usability == 85

    @pytest.mark.asyncio
    async def test_critique_includes_data_in_prompt(self, mock_critic_response):
        with patch("trireason.agents.critic.critic.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_critic_response

            await critique(
                data="specific test data",
                objective="test objective",
                candidate_output="test output",
            )

            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "specific test data" in user_msg
            assert "test output" in user_msg


class TestRefiner:
    @pytest.mark.asyncio
    async def test_refine_continue(self, mock_refiner_response_continue):
        with patch("trireason.agents.refiner.refiner.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_refiner_response_continue

            result = await refine(
                current_system_message="original prompt",
                objective="objective",
                data="data",
                critic_feedback={"issues": ["Missing analysis"], "recommendations": ["Add analysis"]},
            )

            assert "trend analysis" in result.refined_prompt
            assert result.action == "continue"
            assert len(result.changes_made) == 1
            assert result.changes_made[0] == "Added trend analysis requirement"

    @pytest.mark.asyncio
    async def test_refine_stop(self, mock_refiner_response_stop):
        with patch("trireason.agents.refiner.refiner.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_refiner_response_stop

            result = await refine(
                current_system_message="original prompt",
                objective="objective",
                data="data",
                critic_feedback={"issues": ["Minor issue"], "recommendations": ["Fix formatting"]},
            )

            assert result.action == "stop"
            assert result.reason == "no_improvement"

    @pytest.mark.asyncio
    async def test_refine_includes_feedback(self, mock_refiner_response_continue):
        with patch("trireason.agents.refiner.refiner.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_refiner_response_continue

            critic_feedback = {
                "issues": ["Issue 1", "Issue 2"],
                "recommendations": ["Rec 1", "Rec 2"],
                "score_total": 75.0,
            }

            await refine(
                current_system_message="original",
                objective="objective",
                data="data",
                critic_feedback=critic_feedback,
            )

            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "Issue 1" in user_msg or "issues" in user_msg.lower()

    @pytest.mark.asyncio
    async def test_refine_with_quality_threshold(self, mock_refiner_response_continue):
        with patch("trireason.agents.refiner.refiner.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_refiner_response_continue

            await refine(
                current_system_message="original",
                objective="objective",
                data="data",
                critic_feedback={"issues": [], "recommendations": []},
                quality_threshold=95,
            )

            call_args = mock_chat.call_args
            user_msg = call_args[0][1]
            assert "95" in user_msg
