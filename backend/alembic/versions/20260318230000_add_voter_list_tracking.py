"""Add voter_list_uploads, region_schemas tables and tracking fields

Revision ID: 20260318230000
Revises: 20260317140000
Create Date: 2026-03-18

Phase 13: Voter List Tracking + Dashboard Progress
- Creates voter_list_uploads table for tracking upload history
- Creates region_schemas table for CSV column mapping
- Adds tracking fields to registered_voters table
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260318230000"
down_revision: str | Sequence[str] | None = "20260317140000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voter_list_uploads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "region_id", sa.String(36), sa.ForeignKey("regions.id"), nullable=False
        ),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("uploaded_at", sa.DateTime, nullable=False),
        sa.Column("superseded_at", sa.DateTime, nullable=True),
        sa.Column(
            "superseded_by",
            sa.String(36),
            sa.ForeignKey("voter_list_uploads.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_voter_list_uploads_region_id", "voter_list_uploads", ["region_id"]
    )

    op.create_table(
        "region_schemas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "region_id",
            sa.String(36),
            sa.ForeignKey("regions.id"),
            unique=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("column_mappings", sa.JSON, server_default="{}"),
        sa.Column("hash_fields", sa.JSON, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_region_schemas_region_id", "region_schemas", ["region_id"])

    op.add_column(
        "registered_voters", sa.Column("data_hash", sa.String(64), nullable=True)
    )
    op.add_column(
        "registered_voters", sa.Column("first_seen_at", sa.DateTime, nullable=True)
    )
    op.add_column(
        "registered_voters", sa.Column("last_seen_at", sa.DateTime, nullable=True)
    )
    op.add_column(
        "registered_voters",
        sa.Column(
            "first_upload_id",
            sa.String(36),
            sa.ForeignKey("voter_list_uploads.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "registered_voters",
        sa.Column(
            "last_upload_id",
            sa.String(36),
            sa.ForeignKey("voter_list_uploads.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_registered_voters_data_hash", "registered_voters", ["data_hash"]
    )

    op.execute("""
		UPDATE registered_voters
		SET first_seen_at = created_at,
			last_seen_at = COALESCE(updated_at, created_at)
		WHERE first_seen_at IS NULL
	""")


def downgrade() -> None:
    op.drop_index("ix_registered_voters_data_hash", "registered_voters")
    op.drop_column("registered_voters", "last_upload_id")
    op.drop_column("registered_voters", "first_upload_id")
    op.drop_column("registered_voters", "last_seen_at")
    op.drop_column("registered_voters", "first_seen_at")
    op.drop_column("registered_voters", "data_hash")
    op.drop_index("ix_region_schemas_region_id", "region_schemas")
    op.drop_table("region_schemas")
    op.drop_index("ix_voter_list_uploads_region_id", "voter_list_uploads")
    op.drop_table("voter_list_uploads")
