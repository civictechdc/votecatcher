"""Add voter_list_uploads table and tracking fields

Revision ID: 20260318230000
Revises: 20260317140000
Create Date: 2026-03-18

Phase 13: Voter List Tracking + Dashboard Progress
- Creates voter_list_uploads table for tracking upload history
- Adds tracking fields to registered_voters table

Corrective edit (pre-release): this revision never applied on any
alembic-tracked database — the chain aborted at 20260317140000 before
reaching it, and runtime provisioning used create_all, which does not
track alembic_version.
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "20260318230000"
down_revision: str | Sequence[str] | None = "20260317140000"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Batch mode needs names for unnamed reflected FK constraints; SQLite
# leaves FK constraints unnamed, so name them on re-render.
_BATCH_NAMING_CONVENTION = {
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}

_UPLOAD_ID_COLUMNS = (
    sa.Column(
        "first_upload_id",
        sa.Uuid(),
        sa.ForeignKey("voter_list_uploads.id"),
        nullable=True,
    ),
    sa.Column(
        "last_upload_id",
        sa.Uuid(),
        sa.ForeignKey("voter_list_uploads.id"),
        nullable=True,
    ),
)


def _is_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _add_upload_id_columns() -> None:
    for column in _UPLOAD_ID_COLUMNS:
        # inline_references renders the FK within ADD COLUMN itself, which
        # SQLite requires (it cannot ALTER-add constraints separately).
        op.add_column("registered_voters", column, inline_references=True)


def _set_tracking_timestamps_not_null() -> None:
    if _is_sqlite():
        with op.batch_alter_table(
            "registered_voters", naming_convention=_BATCH_NAMING_CONVENTION
        ) as batch_op:
            batch_op.alter_column(
                "first_seen_at", existing_type=sa.DateTime(), nullable=False
            )
            batch_op.alter_column(
                "last_seen_at", existing_type=sa.DateTime(), nullable=False
            )
        return
    op.alter_column(
        "registered_voters",
        "first_seen_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )
    op.alter_column(
        "registered_voters", "last_seen_at", existing_type=sa.DateTime(), nullable=False
    )


def _set_tracking_timestamps_nullable() -> None:
    if _is_sqlite():
        with op.batch_alter_table(
            "registered_voters", naming_convention=_BATCH_NAMING_CONVENTION
        ) as batch_op:
            batch_op.alter_column(
                "first_seen_at", existing_type=sa.DateTime(), nullable=True
            )
            batch_op.alter_column(
                "last_seen_at", existing_type=sa.DateTime(), nullable=True
            )
        return
    op.alter_column(
        "registered_voters", "first_seen_at", existing_type=sa.DateTime(), nullable=True
    )
    op.alter_column(
        "registered_voters", "last_seen_at", existing_type=sa.DateTime(), nullable=True
    )


def upgrade() -> None:
    op.create_table(
        "voter_list_uploads",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("region_id", sa.Uuid(), sa.ForeignKey("regions.id"), nullable=False),
        sa.Column(
            "original_filename", sqlmodel.sql.sqltypes.AutoString(), nullable=False
        ),
        sa.Column("file_size", sa.Integer, nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUPERSEDED", name="uploadstatus"),
            nullable=False,
        ),
        sa.Column("uploaded_at", sa.DateTime, nullable=False),
        sa.Column("superseded_at", sa.DateTime, nullable=True),
        sa.Column(
            "superseded_by",
            sa.Uuid(),
            sa.ForeignKey("voter_list_uploads.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_voter_list_uploads_region_id", "voter_list_uploads", ["region_id"]
    )

    op.add_column(
        "registered_voters",
        sa.Column("data_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.add_column(
        "registered_voters", sa.Column("first_seen_at", sa.DateTime, nullable=True)
    )
    op.add_column(
        "registered_voters", sa.Column("last_seen_at", sa.DateTime, nullable=True)
    )
    _add_upload_id_columns()
    op.create_index(
        "ix_registered_voters_data_hash", "registered_voters", ["data_hash"]
    )

    op.execute("""
		UPDATE registered_voters
		SET first_seen_at = created_at,
			last_seen_at = COALESCE(updated_at, created_at)
		WHERE first_seen_at IS NULL
	""")

    _set_tracking_timestamps_not_null()


def _drop_upload_id_columns() -> None:
    columns = ["last_upload_id", "first_upload_id"]
    if _is_sqlite():
        # SQLite cannot DROP COLUMN when it participates in a foreign key;
        # recreate the table via batch mode instead.
        with op.batch_alter_table(
            "registered_voters", naming_convention=_BATCH_NAMING_CONVENTION
        ) as batch_op:
            for name in columns:
                batch_op.drop_column(name)
        return
    for name in columns:
        op.drop_column("registered_voters", name)


def downgrade() -> None:
    _set_tracking_timestamps_nullable()
    op.drop_index("ix_registered_voters_data_hash", "registered_voters")
    _drop_upload_id_columns()
    op.drop_column("registered_voters", "last_seen_at")
    op.drop_column("registered_voters", "first_seen_at")
    op.drop_column("registered_voters", "data_hash")
    op.drop_index("ix_voter_list_uploads_region_id", "voter_list_uploads")
    op.drop_table("voter_list_uploads")
    if op.get_bind().dialect.name == "postgresql":
        op.execute("DROP TYPE IF EXISTS uploadstatus")
