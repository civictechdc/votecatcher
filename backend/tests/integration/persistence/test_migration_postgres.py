"""Migration-chain tests against a real PostgreSQL database.

Skipped unless TEST_DATABASE_URL is set (CI wires a postgres service);
the URL should point at a disposable database, e.g.
``postgresql://ci:ci@localhost:5432/ci``.  # pragma: allowlist secret
"""

import os
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import urlparse

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

BACKEND_DIR = Path(__file__).parents[3]

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")

_SAFE_HOSTS = {"localhost", "127.0.0.1", "::1"}
_SAFE_DB_MARKERS = ("ci", "test")

if TEST_DATABASE_URL:
    parsed = urlparse(TEST_DATABASE_URL)
    if parsed.hostname not in _SAFE_HOSTS or not any(
        marker in (parsed.path or "/").lstrip("/") for marker in _SAFE_DB_MARKERS
    ):
        raise RuntimeError(
            f"Refusing to run destructive migration tests against "
            f"{TEST_DATABASE_URL!r}: host must be localhost/127.0.0.1/::1 "
            f"and the database name must contain 'ci' or 'test'."
        )

pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL not set; PostgreSQL migration tests skipped",
)

# Supabase browser/API roles hardened against by 20261112000000.
_HARDENED_ROLES = ("anon", "authenticated")


@pytest.fixture()
def pg_engine(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Fresh PostgreSQL database: wipe the schema before each test.

    Pins DATABASE_URL to the test database so alembic's env.py override
    cannot send migrations to the process-wide default.
    """
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    admin = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    admin.dispose()
    yield
    admin.dispose()


def _upgrade(revision: str = "head") -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    cfg.attributes["configure_logger"] = False
    command.upgrade(cfg, revision)


class TestPostgresMigrationChain:
    def test_fresh_chain_reaches_head_and_is_idempotent(self, pg_engine):
        _upgrade()
        _upgrade()

    def test_jobstatus_enum_contains_cancelled(self, pg_engine):
        _upgrade()
        admin = create_engine(TEST_DATABASE_URL)
        with admin.connect() as conn:
            enums = (
                conn.execute(text("SELECT unnest(enum_range(NULL::jobstatus))"))
                .scalars()
                .all()
            )
        admin.dispose()
        assert "CANCELLED" in enums

    def test_no_unique_on_crop_id(self, pg_engine):
        _upgrade()
        admin = create_engine(TEST_DATABASE_URL)
        with admin.connect() as conn:
            constraints = (
                conn.execute(
                    text(
                        "SELECT conname FROM pg_constraint WHERE conrelid "
                        "= 'ocr_results'::regclass AND contype = 'u'"
                    )
                )
                .scalars()
                .all()
            )
            indexes = (
                conn.execute(
                    text(
                        "SELECT idx.relname FROM pg_index ix "
                        "JOIN pg_class idx ON idx.oid = ix.indexrelid "
                        "WHERE ix.indrelid = 'ocr_results'::regclass "
                        "AND ix.indisunique AND NOT ix.indisprimary"
                    )
                )
                .scalars()
                .all()
            )
        admin.dispose()
        assert constraints == []
        assert indexes == []

    def test_multi_column_unique_on_crop_id_ocr_job_id_survives(self, pg_engine):
        """Over-drop guard: uniqueness on more than crop_id must survive."""
        _upgrade("20260312210000")
        admin = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(
                text(
                    "ALTER TABLE ocr_results ADD CONSTRAINT "
                    "uq_ocr_results_crop_ocr_job UNIQUE (crop_id, ocr_job_id)"
                )
            )
        _upgrade()
        with admin.connect() as conn:
            surviving = (
                conn.execute(
                    text(
                        "SELECT conname FROM pg_constraint WHERE conrelid "
                        "= 'ocr_results'::regclass AND contype = 'u'"
                    )
                )
                .scalars()
                .all()
            )
        admin.dispose()
        assert surviving == ["uq_ocr_results_crop_ocr_job"]

    def test_llm_provider_config_hardening(self, pg_engine, monkeypatch):
        """The REVOKE branch must be provable on plain CI PostgreSQL:
        re-create broad grants, re-run the hardening, assert they are gone."""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "vc_head_migration",
            str(
                BACKEND_DIR
                / "alembic"
                / "versions"
                / "20261112000000_add_llm_provider_config_and_model_indexes.py"
            ),
        )
        assert spec is not None and spec.loader is not None
        head = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(head)

        _upgrade()
        admin = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
        created_roles: list[str] = []
        try:
            with admin.connect() as conn:
                for role in _HARDENED_ROLES:
                    exists = conn.execute(
                        text("SELECT 1 FROM pg_roles WHERE rolname = :role"),
                        {"role": role},
                    ).first()
                    if not exists:
                        conn.execute(text(f"CREATE ROLE {role} NOLOGIN"))
                        created_roles.append(role)
                    conn.execute(text(f"GRANT ALL ON llm_provider_config TO {role}"))
                    conn.execute(
                        text(
                            "GRANT ALL ON SEQUENCE llm_provider_config_id_seq "
                            f"TO {role}"
                        )
                    )
                # Simulate Supabase-style PUBLIC grants too.
                conn.execute(text("GRANT ALL ON llm_provider_config TO PUBLIC"))
                conn.execute(
                    text("GRANT ALL ON SEQUENCE llm_provider_config_id_seq TO PUBLIC")
                )
                pre_grants = conn.execute(
                    text(
                        "SELECT grantee, privilege_type FROM information_schema."
                        "role_table_grants WHERE table_name = 'llm_provider_config' "
                        "AND (grantee IN ('anon', 'authenticated') "
                        "OR grantee = 'PUBLIC')"
                    )
                ).fetchall()
                assert pre_grants, "grants must exist before hardening re-runs"

            # Re-run the exact migration hardening code.
            engine = create_engine(TEST_DATABASE_URL)
            with engine.begin() as conn:
                head._harden_llm_provider_config(conn)
            engine.dispose()

            with admin.connect() as conn:
                rls = conn.execute(
                    text(
                        "SELECT relrowsecurity FROM pg_class WHERE relname "
                        "= 'llm_provider_config'"
                    )
                ).scalar()
                table_grants = conn.execute(
                    text(
                        "SELECT grantee, privilege_type FROM information_schema."
                        "role_table_grants WHERE table_name = 'llm_provider_config' "
                        "AND (grantee IN ('anon', 'authenticated') "
                        "OR grantee = 'PUBLIC')"
                    )
                ).fetchall()
                sequence_privileges = {}
                for role in _HARDENED_ROLES:
                    sequence_privileges[role] = conn.execute(
                        text(
                            "SELECT has_sequence_privilege(:role, "
                            "'llm_provider_config_id_seq', 'USAGE,SELECT')"
                        ),
                        {"role": role},
                    ).scalar()
                # PUBLIC is a pseudo-role: query its grants via the
                # information schema instead of has_sequence_privilege.
                public_sequence_grants = conn.execute(
                    text(
                        "SELECT privilege_type FROM information_schema."
                        "role_usage_grants WHERE object_name "
                        "= 'llm_provider_config_id_seq' AND grantee = 'PUBLIC'"
                    )
                ).fetchall()
        finally:
            with admin.connect() as conn:
                for role in created_roles:
                    conn.execute(text(f"DROP ROLE {role}"))
        admin.dispose()
        assert rls is True
        assert table_grants == []
        assert not any(sequence_privileges.values())
        assert public_sequence_grants == []

    def test_standalone_unique_index_on_crop_id_is_removed(self, pg_engine):
        """Negative case: a stray unique index on crop_id (e.g. hand-made on
        a pre-existing database) must be removed by the chain."""
        _upgrade("20260312210000")
        admin = create_engine(TEST_DATABASE_URL, isolation_level="AUTOCOMMIT")
        with admin.connect() as conn:
            conn.execute(
                text(
                    "CREATE UNIQUE INDEX ux_ocr_results_crop_id "
                    "ON ocr_results (crop_id)"
                )
            )
        _upgrade()
        with admin.connect() as conn:
            leftovers = (
                conn.execute(
                    text(
                        "SELECT idx.relname FROM pg_index ix "
                        "JOIN pg_class idx ON idx.oid = ix.indexrelid "
                        "WHERE ix.indrelid = 'ocr_results'::regclass "
                        "AND ix.indisunique AND NOT ix.indisprimary "
                        "AND idx.relname = 'ux_ocr_results_crop_id'"
                    )
                )
                .scalars()
                .all()
            )
        admin.dispose()
        assert leftovers == []
