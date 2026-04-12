"""Unit tests for ConfigService.

BDD-style tests describing expected behaviour of the config service
before the implementation exists. Written using vertical-slice TDD: one test →
implement → verify → next.
"""

import pytest
from sqlalchemy import text
from sqlmodel import Session, create_engine

RESET_TABLES = [
    "campaigns",
    "match_results",
    "ocr_results",
    "ocr_jobs",
    "matcher_jobs",
    "petition_crops",
    "petition_scans",
]


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    with engine.connect() as conn:
        for table in RESET_TABLES:
            conn.execute(
                text(f"CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY)")
            )
        conn.commit()
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


def _seed_rows(session: Session, table: str, count: int = 3):
    for i in range(count):
        session.exec(text(f"INSERT INTO {table} DEFAULT VALUES"))
    session.commit()


class TestResetAllData:
    """Feature: Data reset.

    As an API consumer
    I want to reset all application data
    So that I can clear the database in non-production environments.
    """

    def test_deletes_rows_from_all_tables_and_returns_counts(self, session: Session):
        """Scenario: Tables have rows, reset deletes all and returns accurate counts."""
        from app.services.config_service import ConfigService

        _seed_rows(session, "campaigns", 5)
        _seed_rows(session, "match_results", 3)
        _seed_rows(session, "ocr_results", 7)
        _seed_rows(session, "ocr_jobs", 2)
        _seed_rows(session, "matcher_jobs", 1)
        _seed_rows(session, "petition_crops", 4)
        _seed_rows(session, "petition_scans", 6)

        service = ConfigService(session)
        result = service.reset_all_data()

        assert result["campaigns"] == 5
        assert result["match_results"] == 3
        assert result["ocr_results"] == 7
        assert result["ocr_jobs"] == 2
        assert result["matcher_jobs"] == 1
        assert result["petition_crops"] == 4
        assert result["petition_scans"] == 6

        for table in RESET_TABLES:
            remaining = session.exec(text(f"SELECT COUNT(*) FROM {table}")).one()
            assert remaining[0] == 0

    def test_returns_zero_counts_for_empty_tables(self, session: Session):
        """Scenario: All tables are empty, reset returns zeros."""
        from app.services.config_service import ConfigService

        service = ConfigService(session)
        result = service.reset_all_data()

        for table in RESET_TABLES:
            assert result[table] == 0

    def test_commits_transaction(self, session: Session):
        """Scenario: Reset commits so deletions persist beyond the service call."""
        from app.services.config_service import ConfigService

        _seed_rows(session, "campaigns", 2)

        service = ConfigService(session)
        service.reset_all_data()

        remaining = session.exec(text("SELECT COUNT(*) FROM campaigns")).one()
        assert remaining[0] == 0
