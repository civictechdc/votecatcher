"""Add force_reprocess, cached_ocr_count, new_ocr_count to matcher_jobs

Revision ID: 20260312210000
Revises: 20260312200000
Create Date: 2026-03-12

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260312210000"
down_revision: str | Sequence[str] | None = "20260312200000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
	op.add_column(
		"matcher_jobs",
		sa.Column("force_reprocess", sa.Boolean(), nullable=False, server_default="0"),
	)
	op.add_column(
		"matcher_jobs",
		sa.Column("cached_ocr_count", sa.Integer(), nullable=True),
	)
	op.add_column(
		"matcher_jobs",
		sa.Column("new_ocr_count", sa.Integer(), nullable=True),
	)


def downgrade() -> None:
	op.drop_column("matcher_jobs", "new_ocr_count")
	op.drop_column("matcher_jobs", "cached_ocr_count")
	op.drop_column("matcher_jobs", "force_reprocess")
