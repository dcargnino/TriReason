"""Tests for the FastAPI API endpoints."""

import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from trireason.app import create_app
from trireason.schemas.optimization import (
    IterationResponse,
    OptimizationResponse,
    ScoreBreakdown,
)


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_optimization_response():
    run_id = uuid.uuid4()
    breakdown = ScoreBreakdown(
        objective_fulfillment=92,
        correctness_faithfulness=88,
        completeness=85,
        format_compliance=95,
        clarity_usability=90,
    )
    return OptimizationResponse(
        run_id=run_id,
        status="completed",
        total_iterations=2,
        best_score=90.5,
        best_prompt="Optimized prompt here",
        stop_reason="threshold_reached",
        iterations=[
            IterationResponse(
                iteration_number=1,
                candidate_prompt="first prompt",
                candidate_output="first output",
                score_total=75.0,
                score_breakdown=breakdown,
                passed=False,
                issues=["needs improvement"],
                recommendations=["add details"],
                is_best_so_far=True,
            ),
            IterationResponse(
                iteration_number=2,
                candidate_prompt="Optimized prompt here",
                candidate_output="better output",
                score_total=90.5,
                score_breakdown=breakdown,
                passed=True,
                issues=[],
                recommendations=[],
                is_best_so_far=True,
            ),
        ],
    )


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "trireason"


class TestOptimizeEndpoint:
    @pytest.mark.asyncio
    async def test_optimize_success(self, client, mock_optimization_response):
        with patch(
            "trireason.api.routes.run_and_persist",
            new_callable=AsyncMock,
            return_value=mock_optimization_response,
        ):
            response = await client.post(
                "/api/v1/optimize",
                json={
                    "data": "test data",
                    "objective": "test objective",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["best_score"] == 90.5
            assert len(data["iterations"]) == 2

    @pytest.mark.asyncio
    async def test_optimize_validation_error(self, client):
        response = await client.post(
            "/api/v1/optimize",
            json={"data": "test"},  # missing objective
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_optimize_custom_params(self, client, mock_optimization_response):
        with patch(
            "trireason.api.routes.run_and_persist",
            new_callable=AsyncMock,
            return_value=mock_optimization_response,
        ) as mock_run:
            response = await client.post(
                "/api/v1/optimize",
                json={
                    "data": "data",
                    "objective": "obj",
                    "max_iterations": 10,
                    "score_threshold": 90,
                    "constraints": {"language": "Italian"},
                },
            )
            assert response.status_code == 200
            call_kwargs = mock_run.call_args
            assert call_kwargs.kwargs["max_iterations"] == 10
            assert call_kwargs.kwargs["score_threshold"] == 90


class TestGetRunEndpoint:
    @pytest.mark.asyncio
    async def test_run_not_found(self, client):
        with patch(
            "trireason.api.routes.get_cached_run",
            new_callable=AsyncMock,
            return_value=None,
        ), patch(
            "trireason.api.routes.repo.get_run",
            new_callable=AsyncMock,
            return_value=None,
        ):
            run_id = uuid.uuid4()
            response = await client.get(f"/api/v1/runs/{run_id}")
            assert response.status_code == 404
