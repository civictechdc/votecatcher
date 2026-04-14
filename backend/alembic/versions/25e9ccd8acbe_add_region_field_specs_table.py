"""add region_field_specs table

Revision ID: 25e9ccd8acbe
Revises: 20260327010000
Create Date: 2026-04-13 20:19:36.590387

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "25e9ccd8acbe"  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = "20260327010000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "region_field_specs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("region_id", sa.String(), nullable=False),
        sa.Column("region_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("ballot_fields", sa.JSON(), nullable=True),
        sa.Column("voter_reg_fields", sa.JSON(), nullable=True),
        sa.Column("field_mappings", sa.JSON(), nullable=True),
        sa.Column("hash_fields", sa.JSON(), nullable=True),
        sa.Column("crop_config", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("region_id"),
        sa.UniqueConstraint("region_key"),
    )
    op.create_index(
        op.f("ix_region_field_specs_region_id"),
        "region_field_specs",
        ["region_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_region_field_specs_region_key"),
        "region_field_specs",
        ["region_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_region_field_specs_region_key"), table_name="region_field_specs"
    )
    op.drop_index(
        op.f("ix_region_field_specs_region_id"), table_name="region_field_specs"
    )
    op.drop_table("region_field_specs")
