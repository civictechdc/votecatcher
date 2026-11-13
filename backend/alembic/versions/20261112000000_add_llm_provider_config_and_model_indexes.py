"""Add llm_provider_config table, petition_scans.file_size, and model indexes

Brings the migration chain to full parity with the runtime model set
(app.persistence.engines.model_imports.import_models):

- Creates the llm_provider_config table (model had no migration), with
  PostgreSQL hardening: RLS enabled (not FORCED, so the table owner the
  app connects as keeps working) and grants revoked from anon,
  authenticated, and PUBLIC — deny-by-default for Supabase browser/API
  roles, including their default sequence grants
- Adds petition_scans.file_size (present in model, absent from chain)
- Creates the indexes declared on the models (single-column and the
  composite ix_match_results_job_ocr / idx_ocr_results_crop_index pairs)
- Adds the CANCELLED value to the jobstatus enum on PostgreSQL
  (JobStatus.CANCELLED is written by job cancellation flows)

Revision ID: 20261112000000
Revises: 7a5f1e454eac
Create Date: 2026-11-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlalchemy.engine
import sqlmodel

from alembic import op

revision: str = "20261112000000"
down_revision: str | Sequence[str] | None = "7a5f1e454eac"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Supabase browser/API roles; they exist on Supabase, not on a plain
# PostgreSQL instance.
_SUPABASE_ROLES = ("anon", "authenticated")


def _harden_llm_provider_config(bind: sa.engine.Connection) -> None:
    """Deny-by-default for Supabase browser/API roles.

    llm_provider_config stores provider API keys, and Supabase projects
    grant anon and authenticated broad access including the Data API.
    RLS with no policies plus revoked grants blocks those roles entirely.
    RLS is not FORCED so the table owner (the role the app connects as)
    keeps working.
    """
    bind.execute(sa.text("ALTER TABLE llm_provider_config ENABLE ROW LEVEL SECURITY"))
    bind.execute(sa.text("REVOKE ALL ON llm_provider_config FROM PUBLIC"))
    # Revoke per role so one absent role cannot skip the other's revoke.
    for role in _SUPABASE_ROLES:
        bind.execute(
            sa.text(
                f"""DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                        REVOKE ALL ON llm_provider_config FROM {role};
                    END IF;
                END
                $$;"""
            )
        )
    # The id column renders as SERIAL on PostgreSQL, so the sequence exists;
    # Supabase grants default sequence privileges to those roles too.
    bind.execute(
        sa.text("REVOKE ALL ON SEQUENCE llm_provider_config_id_seq FROM PUBLIC")
    )
    for role in _SUPABASE_ROLES:
        bind.execute(
            sa.text(
                f"""DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
                        REVOKE ALL ON SEQUENCE llm_provider_config_id_seq FROM {role};
                    END IF;
                END
                $$;"""
            )
        )


def upgrade() -> None:
    op.create_table(
        "llm_provider_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("api_key", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("model", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_configured", sa.Boolean(), nullable=False),
        sa.Column("last_validated", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_llm_provider_config_provider",
        "llm_provider_config",
        ["provider"],
        unique=True,
    )
    op.add_column("petition_scans", sa.Column("file_size", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_match_results_matcher_job_id"),
        "match_results",
        ["matcher_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_match_results_job_ocr",
        "match_results",
        ["matcher_job_id", "ocr_result_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_match_results_ocr_result_id"),
        "match_results",
        ["ocr_result_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_match_results_voter_id"),
        "match_results",
        ["voter_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_ocr_results_crop_id"), "ocr_results", ["crop_id"], unique=False
    )
    op.create_index(
        op.f("ix_ocr_results_ocr_job_id"),
        "ocr_results",
        ["ocr_job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_petition_crops_scan_id"), "petition_crops", ["scan_id"], unique=False
    )
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE jobstatus ADD VALUE IF NOT EXISTS 'CANCELLED'")
        _harden_llm_provider_config(op.get_bind())


def downgrade() -> None:
    # The CANCELLED value added to jobstatus in upgrade() is intentionally
    # retained: PostgreSQL cannot DROP enum values.
    op.drop_index(op.f("ix_petition_crops_scan_id"), table_name="petition_crops")
    op.drop_index(op.f("ix_ocr_results_ocr_job_id"), table_name="ocr_results")
    op.drop_index(op.f("ix_ocr_results_crop_id"), table_name="ocr_results")
    op.drop_index(op.f("ix_match_results_voter_id"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_ocr_result_id"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_matcher_job_id"), table_name="match_results")
    op.drop_index("ix_match_results_job_ocr", table_name="match_results")
    op.drop_column("petition_scans", "file_size")
    op.drop_index("ix_llm_provider_config_provider", table_name="llm_provider_config")
    op.drop_table("llm_provider_config")
