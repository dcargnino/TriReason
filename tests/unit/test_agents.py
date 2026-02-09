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
def mock_refiner_response():
    return json.dumps({
        "refined_prompt": "You are a senior data analyst. Provide a detailed summary with trend analysis.",
        "changes_made": ["Added trend analysis requirement"],
    })


class TestGenerator:
    @pytest.mark.asyncio
    async def test_generate_initial(self, mock_generator_response):
        with patch("trireason.agents.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response

            result = await generate_initial(
                data="Sales: Jan=$100k, Feb=$110k",
                objective="Summarize sales trends",
            )

            assert result.candidate_prompt is not None
            assert result.candidate_output is not None
            mock_chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_initial_with_constraints(self, mock_generator_response):
        with patch("trireason.agents.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response

            result = await generate_initial(
                data="data",
                objective="objective",
                constraints={"format": "bullet points"},
            )

            assert result.candidate_prompt is not None
            # Verify constraints were included in the call
            call_args = mock_chat.call_args
            assert "CONSTRAINTS" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_generate_from_refinement(self, mock_generator_response):
        with patch("trireason.agents.generator.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_generator_response

            result = await generate_from_refinement(
                data="data",
                objective="objective",
                refined_prompt="improved prompt",
                critic_issues=["issue1"],
            )

            assert result.candidate_prompt is not None
            assert result.candidate_output is not None


class TestCritic:
    @pytest.mark.asyncio
    async def test_critique(self, mock_critic_response):
        with patch("trireason.agents.critic.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_critic_response

            result = await critique(
                data="data",
                objective="objective",
                candidate_prompt="prompt",
                candidate_output="output",
                threshold=85,
            )

            assert result.score_total == 82.0
            assert result.passed is False
            assert len(result.issues) == 1
            assert result.score_breakdown.objective_fulfillment == 85

    @pytest.mark.asyncio
    async def test_critique_passing(self):
        passing_response = json.dumps({
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
        with patch("trireason.agents.critic.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = passing_response

            result = await critique(
                data="data",
                objective="objective",
                candidate_prompt="prompt",
                candidate_output="output",
            )

            assert result.passed is True
            assert result.score_total == 92.0


class TestRefiner:
    @pytest.mark.asyncio
    async def test_refine(self, mock_refiner_response):
        with patch("trireason.agents.refiner.chat_json", new_callable=AsyncMock) as mock_chat:
            mock_chat.return_value = mock_refiner_response

            result = await refine(
                current_prompt="original prompt",
                objective="objective",
                issues=["Missing analysis"],
                recommendations=["Add trend analysis"],
                score_total=75.0,
            )

            assert "trend analysis" in result.refined_prompt
            assert len(result.changes_made) == 1
