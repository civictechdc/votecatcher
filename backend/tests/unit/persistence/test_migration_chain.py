"""Behavioral tests for the Alembic migration chain on a fresh database.

The runtime provisions databases through `alembic upgrade head`
(SupabaseEngine) or SQLModel create_all (SQLite engine), so the chain must
both run cleanly from scratch and land on a schema that matches the
canonical runtime model set.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

BACKEND_DIR = Path(__file__).parents[3]


def _make_config(db_path: Path) -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    # Keep alembic from reconfiguring pytest's logging.
    cfg.attributes["configure_logger"] = False
    return cfg


@pytest.fixture()
def fresh_db_upgrade(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Run the full migration chain against a fresh SQLite database."""
    db_path = tmp_path / "migration-chain.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    cfg = _make_config(db_path)
    command.upgrade(cfg, "head")
    return cfg, create_engine(f"sqlite:///{db_path}")


class TestMigrationChain:
    def test_chain_reaches_head(self, fresh_db_upgrade):
        cfg, _ = fresh_db_upgrade
        head = ScriptDirectory.from_config(cfg).get_current_head()
        assert head is not None

    def test_second_upgrade_is_noop(self, fresh_db_upgrade):
        cfg, engine = fresh_db_upgrade
        head = ScriptDirectory.from_config(cfg).get_current_head()

        command.upgrade(cfg, "head")

        with engine.connect() as conn:
            version = conn.exec_driver_sql(
                "SELECT version_num FROM alembic_version"
            ).scalar()
        assert version == head

    def test_ocr_results_crop_id_is_not_unique(self, fresh_db_upgrade):
        """crop_id must not be unique so multiple OCR entries per crop persist."""
        _, engine = fresh_db_upgrade
        inspector = inspect(engine)
        unique_columns = [
            constraint["column_names"]
            for constraint in inspector.get_unique_constraints("ocr_results")
        ]
        assert ["crop_id"] not in unique_columns

    def test_seeded_data_survives_upgrade_to_head(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        """Rows seeded at 20260312210000 must survive the batch rebuilds and
        backfills of the later revisions, and multiple OCR entries per crop
        must be storable afterwards."""
        db_path = tmp_path / "seeded-chain.db"
        url = f"sqlite:///{db_path}"
        cfg = _make_config(db_path)

        monkeypatch.setenv("DATABASE_URL", url)
        command.upgrade(cfg, "20260312210000")
        engine = create_engine(url)
        region_id = "5f0e5a58-7d1f-4a2d-9a3e-1a2b3c4d5e6f"
        campaign_id = "6f1f6b69-8e2f-5b3e-0b4f-2b3c4d5e6f7a"
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO regions (id, region_key, region_name, country_code) "
                    "VALUES (:id, 'ca-test', 'Test Region', 'US')"
                ),
                {"id": region_id},
            )
            conn.execute(
                text(
                    "INSERT INTO campaigns (id, created_at, unique_name, title, "
                    "year, region_id) VALUES (:id, '2026-01-01 00:00:00', "
                    "'camp', 'Campaign', '2026', :region_id)"
                ),
                {"id": campaign_id, "region_id": region_id},
            )
            conn.execute(
                text(
                    "INSERT INTO matcher_jobs (id, campaign_id, current_status, "
                    "created_at) VALUES (1, :campaign_id, 'COMPLETED', "
                    "'2026-01-02 00:00:00')"
                ),
                {"campaign_id": campaign_id},
            )
            conn.execute(
                text(
                    "INSERT INTO ocr_jobs (id, matcher_job_id, status, created_at) "
                    "VALUES (1, 1, 'COMPLETED', '2026-01-02 00:00:00')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO petition_scans (id, campaign_id, original_filename, "
                    "stored_path, file_hash, uploaded_at) VALUES (1, :campaign_id, "
                    "'scan.pdf', '/tmp/scan.pdf', 'hash1', '2026-01-02 00:00:00')"
                ),
                {"campaign_id": campaign_id},
            )
            conn.execute(
                text(
                    "INSERT INTO petition_crops (id, scan_id, crop_index, stored_path, "
                    "page_number, created_at) VALUES (1, 1, 0, '/tmp/crop0.png', 1, "
                    "'2026-01-02 00:00:00')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO ocr_results (id, crop_id, ocr_job_id, created_at) "
                    "VALUES (1, 1, 1, '2026-01-03 00:00:00')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO match_results (id, ocr_result_id, matcher_job_id, "
                    "rank, voter_id, similarity_score, confidence_level, created_at) "
                    "VALUES (1, 1, 1, 1, NULL, 0.9, 'HIGH', '2026-01-03 00:00:00')"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO registered_voters (id, region_id, created_at, "
                    "updated_at) VALUES (1, :region_id, '2026-01-04 10:30:00', "
                    "'2026-01-05 11:00:00')"
                ),
                {"region_id": region_id},
            )
        engine.dispose()

        command.upgrade(cfg, "head")

        engine = create_engine(url)
        with engine.begin() as conn:
            ocr_rows = conn.execute(
                text("SELECT id, crop_id, ocr_index FROM ocr_results ORDER BY id")
            ).fetchall()
            assert ocr_rows == [(1, 1, 0)]
            match_rows = conn.execute(
                text("SELECT id, matcher_job_id, ocr_result_id FROM match_results")
            ).fetchall()
            assert match_rows == [(1, 1, 1)]
            voter = conn.execute(
                text(
                    "SELECT first_seen_at, last_seen_at FROM registered_voters "
                    "WHERE id = 1"
                )
            ).fetchone()
            assert voter == ("2026-01-04 10:30:00", "2026-01-05 11:00:00")
            # Multiple OCR entries per crop are storable now.
            conn.execute(
                text(
                    "INSERT INTO ocr_results (id, crop_id, ocr_job_id, ocr_index, "
                    "created_at) VALUES (2, 1, 1, 1, '2026-01-03 00:00:00')"
                )
            )
            count = conn.execute(
                text("SELECT count(*) FROM ocr_results WHERE crop_id = 1")
            ).scalar()
            assert count == 2
        inspector = inspect(engine)
        index_names = {i["name"] for i in inspector.get_indexes("ocr_results")}
        assert {"idx_ocr_results_crop_index", "ix_ocr_results_crop_id"} <= index_names
        match_index_names = {i["name"] for i in inspector.get_indexes("match_results")}
        assert "ix_match_results_job_ocr" in match_index_names
        engine.dispose()

    def test_model_indexes_exist(self, fresh_db_upgrade):
        _, engine = fresh_db_upgrade
        inspector = inspect(engine)
        ocr_index_names = {
            index["name"] for index in inspector.get_indexes("ocr_results")
        }
        assert "ix_ocr_results_crop_id" in ocr_index_names
        assert "ix_ocr_results_ocr_job_id" in ocr_index_names

    def test_chain_covers_runtime_model_set(self, fresh_db_upgrade):
        """Tables only reachable via the runtime model set must exist."""
        _, engine = fresh_db_upgrade
        inspector = inspect(engine)
        assert "llm_provider_config" in inspector.get_table_names()
        petition_columns = {
            column["name"] for column in inspector.get_columns("petition_scans")
        }
        assert "file_size" in petition_columns

    def test_tracking_timestamps_are_not_null_after_backfill(self, fresh_db_upgrade):
        _, engine = fresh_db_upgrade
        inspector = inspect(engine)
        columns = {
            column["name"]: column
            for column in inspector.get_columns("registered_voters")
        }
        assert columns["first_seen_at"]["nullable"] is False
        assert columns["last_seen_at"]["nullable"] is False

    def test_downgrade_to_base_revision_and_reupgrade(self, fresh_db_upgrade):
        """Roundtrip head -> c18ff4a97d6e -> head exercises every downgrade,
        including the SQLite batch downgrades and the crop_id unique
        constraint re-create."""
        cfg, engine = fresh_db_upgrade
        head = ScriptDirectory.from_config(cfg).get_current_head()
        assert head is not None

        command.downgrade(cfg, "c18ff4a97d6e")  # pragma: allowlist secret
        with engine.connect() as conn:
            version = conn.exec_driver_sql(
                "SELECT version_num FROM alembic_version"
            ).scalar()
        assert version == "c18ff4a97d6e"  # pragma: allowlist secret

        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            version = conn.exec_driver_sql(
                "SELECT version_num FROM alembic_version"
            ).scalar()
        assert version == head

        inspector = inspect(engine)
        unique_columns = [
            constraint["column_names"]
            for constraint in inspector.get_unique_constraints("ocr_results")
        ]
        assert ["crop_id"] not in unique_columns
