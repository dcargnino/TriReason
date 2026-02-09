"""Initial schema – optimization_runs and iterations tables.

Revision ID: 001
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "optimization_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("user_data", sa.Text, nullable=False),
        sa.Column("user_data_hash", sa.String(64), nullable=False, index=True),
        sa.Column("objective", sa.Text, nullable=False),
        sa.Column("constraints", JSON, nullable=True),
        sa.Column("max_iterations", sa.Integer, nullable=False, server_default="5"),
        sa.Column("score_threshold", sa.Integer, nullable=False, server_default="85"),
        sa.Column("best_iteration", sa.Integer, nullable=True),
        sa.Column("best_score", sa.Float, nullable=True),
        sa.Column("best_prompt", sa.Text, nullable=True),
        sa.Column("stop_reason", sa.String(50), nullable=True),
        sa.Column("total_iterations", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "iterations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("iteration_number", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("candidate_prompt", sa.Text, nullable=False),
        sa.Column("candidate_output", sa.Text, nullable=False),
        sa.Column("score_total", sa.Float, nullable=False),
        sa.Column("score_breakdown", JSON, nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("critic_issues", JSON, nullable=False, server_default="[]"),
        sa.Column("critic_recommendations", JSON, nullable=False, server_default="[]"),
        sa.Column("is_best_so_far", sa.Boolean, nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_table("iterations")
    op.drop_table("optimization_runs")
