"""Core regions, sources, observations, and scenarios.

Revision ID: 0001_core
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_core"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table("regions", sa.Column("id", sa.String(64), primary_key=True), sa.Column("name", sa.String(120), nullable=False), sa.Column("region_type", sa.String(32), nullable=False), sa.Column("state", sa.String(80), nullable=False), sa.Column("area_km2", sa.Float(), nullable=False), sa.Column("centroid", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_regions_state", "regions", ["state"])
    op.create_table("data_sources", sa.Column("id", sa.String(80), primary_key=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("url", sa.String(500)), sa.Column("license", sa.String(160)), sa.Column("source_type", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("observations", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("region_id", sa.String(64), sa.ForeignKey("regions.id"), nullable=False), sa.Column("source_id", sa.String(80), sa.ForeignKey("data_sources.id"), nullable=False), sa.Column("variable", sa.String(80), nullable=False), sa.Column("value", sa.Float(), nullable=False), sa.Column("unit", sa.String(40), nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("quality_score", sa.Float(), nullable=False), sa.Column("attributes", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_observation_region_variable_time", "observations", ["region_id", "variable", "observed_at"])
    op.create_table("scenarios", sa.Column("id", sa.Uuid(), primary_key=True), sa.Column("region_id", sa.String(64), sa.ForeignKey("regions.id"), nullable=False), sa.Column("name", sa.String(100), nullable=False), sa.Column("status", sa.String(32), nullable=False), sa.Column("parameters", sa.JSON(), nullable=False), sa.Column("result", sa.JSON()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_scenarios_region_id", "scenarios", ["region_id"])


def downgrade() -> None:
    op.drop_table("scenarios")
    op.drop_table("observations")
    op.drop_table("data_sources")
    op.drop_table("regions")

