"""Add ocr_duration_seconds and matching_duration_seconds to matcher_jobs

Revision ID: 20260327010000
Revises: 20260318230000
Create Date: 2026-03-27

Adds stage timing fields to track how long OCR and matching phases take.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260327010000"
down_revision: str | Sequence[str] | None = "20260318230000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
	op.add_column(
		"matcher_jobs",
		sa.Column("ocr_duration_seconds", sa.Float(), nullable=True),
	)
	op.add_column(
		"matcher_jobs",
		sa.Column("matching_duration_seconds", sa.Float(), nullable=True),
	)


def downgrade() -> None:
	op.drop_column("matcher_jobs", "matching_duration_seconds")
	op.drop_column("matcher_jobs", "ocr_duration_seconds")
