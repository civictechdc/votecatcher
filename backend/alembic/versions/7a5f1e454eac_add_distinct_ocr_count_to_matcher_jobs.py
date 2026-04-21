"""add_distinct_ocr_count_to_matcher_jobs

Revision ID: 7a5f1e454eac
Revises: 25e9ccd8acbe
Create Date: 2026-04-21 15:12:59.717614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a5f1e454eac'
down_revision: Union[str, Sequence[str], None] = '25e9ccd8acbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matcher_jobs",
        sa.Column("distinct_ocr_count", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("matcher_jobs", "distinct_ocr_count")
