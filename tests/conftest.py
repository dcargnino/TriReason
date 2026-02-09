"""Shared test fixtures."""

import pytest

from trireason.schemas.optimization import (
    CriticOutput,
    GeneratorOutput,
    OptimizationRequest,
    RefinerOutput,
    ScoreBreakdown,
)


@pytest.fixture
def sample_request() -> OptimizationRequest:
    return OptimizationRequest(
        data="Monthly sales data for Q1 2025: Jan=$120k, Feb=$135k, Mar=$150k",
        objective="Generate a concise executive summary with trend analysis and forecast",
        max_iterations=3,
        score_threshold=85,
    )


@pytest.fixture
def sample_generator_output() -> GeneratorOutput:
    return GeneratorOutput(
        candidate_prompt="You are a financial analyst. Given the following quarterly sales data, produce a concise executive summary with trend analysis and a forecast for Q2.",
        candidate_output="Q1 2025 Executive Summary: Revenue grew steadily from $120k (Jan) to $150k (Mar), showing 25% quarter-over-quarter growth. The upward trend suggests Q2 could reach $165-180k if momentum continues.",
    )


@pytest.fixture
def sample_score_breakdown() -> ScoreBreakdown:
    return ScoreBreakdown(
        objective_fulfillment=90,
        correctness_faithfulness=85,
        completeness=80,
        format_compliance=95,
        clarity_usability=88,
    )


@pytest.fixture
def sample_critic_output(sample_score_breakdown: ScoreBreakdown) -> CriticOutput:
    return CriticOutput(
        score_total=87.9,
        score_breakdown=sample_score_breakdown,
        passed=True,
        issues=["Forecast lacks confidence intervals"],
        recommendations=["Add confidence intervals to the forecast range"],
    )


@pytest.fixture
def sample_refiner_output() -> RefinerOutput:
    return RefinerOutput(
        refined_prompt="You are a senior financial analyst. Given quarterly sales data, produce a concise executive summary including: 1) Key metrics, 2) Trend analysis with percentage changes, 3) Q2 forecast with confidence intervals. Use bullet points.",
        changes_made=["Added confidence interval requirement", "Specified bullet point format"],
    )
