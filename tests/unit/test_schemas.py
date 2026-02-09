"""Tests for Pydantic schema validation."""

import uuid

import pytest

from trireason.schemas.optimization import (
    CompletionEvent,
    CriticOutput,
    GeneratorOutput,
    IterationEvent,
    IterationResponse,
    OptimizationRequest,
    OptimizationResponse,
    RefinerOutput,
    RunStatusResponse,
    ScoreBreakdown,
)


class TestOptimizationRequest:
    def test_valid_request(self):
        req = OptimizationRequest(
            data="some data",
            objective="some objective",
        )
        assert req.max_iterations == 5
        assert req.score_threshold == 85

    def test_custom_params(self):
        req = OptimizationRequest(
            data="data",
            objective="obj",
            max_iterations=10,
            score_threshold=90,
            constraints={"language": "English"},
        )
        assert req.max_iterations == 10
        assert req.constraints == {"language": "English"}

    def test_max_iterations_bounds(self):
        with pytest.raises(Exception):
            OptimizationRequest(data="d", objective="o", max_iterations=0)
        with pytest.raises(Exception):
            OptimizationRequest(data="d", objective="o", max_iterations=21)

    def test_score_threshold_bounds(self):
        with pytest.raises(Exception):
            OptimizationRequest(data="d", objective="o", score_threshold=-1)
        with pytest.raises(Exception):
            OptimizationRequest(data="d", objective="o", score_threshold=101)


class TestScoreBreakdown:
    def test_valid_breakdown(self, sample_score_breakdown):
        assert sample_score_breakdown.objective_fulfillment == 90
        assert sample_score_breakdown.clarity_usability == 88

    def test_weighted_total(self, sample_score_breakdown):
        expected = (
            90 * 0.40
            + 85 * 0.25
            + 80 * 0.15
            + 95 * 0.10
            + 88 * 0.10
        )
        assert abs(expected - 87.55) < 0.01


class TestGeneratorOutput:
    def test_valid(self, sample_generator_output):
        assert "financial analyst" in sample_generator_output.candidate_prompt
        assert "Q1 2025" in sample_generator_output.candidate_output


class TestCriticOutput:
    def test_valid(self, sample_critic_output):
        assert sample_critic_output.score_total == 87.9
        assert sample_critic_output.passed is True
        assert len(sample_critic_output.issues) == 1

    def test_score_bounds(self):
        with pytest.raises(Exception):
            CriticOutput(
                score_total=101,
                score_breakdown=ScoreBreakdown(
                    objective_fulfillment=0,
                    correctness_faithfulness=0,
                    completeness=0,
                    format_compliance=0,
                    clarity_usability=0,
                ),
                passed=False,
            )


class TestRefinerOutput:
    def test_valid(self, sample_refiner_output):
        assert "confidence intervals" in sample_refiner_output.refined_prompt
        assert len(sample_refiner_output.changes_made) == 2


class TestIterationResponse:
    def test_construction(self, sample_score_breakdown):
        resp = IterationResponse(
            iteration_number=1,
            candidate_prompt="test prompt",
            candidate_output="test output",
            score_total=88.0,
            score_breakdown=sample_score_breakdown,
            passed=True,
            issues=[],
            recommendations=[],
            is_best_so_far=True,
        )
        assert resp.iteration_number == 1
        assert resp.is_best_so_far is True


class TestOptimizationResponse:
    def test_construction(self, sample_score_breakdown):
        run_id = uuid.uuid4()
        resp = OptimizationResponse(
            run_id=run_id,
            status="completed",
            total_iterations=3,
            best_score=92.5,
            best_prompt="best prompt",
            stop_reason="threshold_reached",
            iterations=[
                IterationResponse(
                    iteration_number=1,
                    candidate_prompt="p",
                    candidate_output="o",
                    score_total=92.5,
                    score_breakdown=sample_score_breakdown,
                    passed=True,
                    issues=[],
                    recommendations=[],
                    is_best_so_far=True,
                )
            ],
        )
        assert resp.run_id == run_id
        assert resp.total_iterations == 3


class TestSSEEvents:
    def test_iteration_event(self, sample_score_breakdown):
        run_id = uuid.uuid4()
        event = IterationEvent(
            run_id=run_id,
            iteration=IterationResponse(
                iteration_number=1,
                candidate_prompt="p",
                candidate_output="o",
                score_total=80.0,
                score_breakdown=sample_score_breakdown,
                passed=False,
                issues=["issue"],
                recommendations=["rec"],
                is_best_so_far=True,
            ),
        )
        assert event.event == "iteration"

    def test_completion_event(self):
        event = CompletionEvent(
            run_id=uuid.uuid4(),
            best_score=90.0,
            best_prompt="best",
            stop_reason="threshold_reached",
            total_iterations=2,
        )
        assert event.event == "complete"
