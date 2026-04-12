"""Add ocr_index column, remove unique constraint on crop_id

Fixes BUG-14: OCR duplicate results issue where only 1 of 5 entries
per crop was being stored due to UNIQUE constraint on crop_id.

- Adds ocr_index column (0-4 for 5 signatures per crop)
- Removes UNIQUE constraint from crop_id
- Sets default ocr_index=0 for backward compatibility

Revision ID: 20260317140000
Revises: 20260312210000
Create Date: 2026-03-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260317140000"
down_revision: str | Sequence[str] | None = "20260312210000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ocr_results",
        sa.Column(
            "ocr_index",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.drop_constraint("crop_id", "ocr_results", type_="unique")
    op.create_index(
        "idx_ocr_results_crop_index",
        "ocr_results",
        ["crop_id", "ocr_index"],
    )


def downgrade() -> None:
    op.drop_index("idx_ocr_results_crop_index", table_name="ocr_results")
    op.create_unique_constraint("crop_id", "ocr_results", ["crop_id"])
    op.drop_column("ocr_results", "ocr_index")
