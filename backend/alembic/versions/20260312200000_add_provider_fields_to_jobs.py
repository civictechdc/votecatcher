"""Add provider_name and provider_model to matcher_jobs

Revision ID: 20260312200000
Revises: c18ff4a97d6e
Create Date: 2026-03-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "20260312200000"
down_revision: str | Sequence[str] | None = "c18ff4a97d6e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add provider_name and provider_model columns to matcher_jobs."""
    op.add_column(
        "matcher_jobs",
        sa.Column("provider_name", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "matcher_jobs",
        sa.Column("provider_model", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    """Remove provider_name and provider_model columns from matcher_jobs."""
    op.drop_column("matcher_jobs", "provider_model")
    op.drop_column("matcher_jobs", "provider_name")
