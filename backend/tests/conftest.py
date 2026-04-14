import os

import pytest
from approvaltests import set_default_reporter
from approvaltests.reporters.python_native_reporter import PythonNativeReporter

os.environ["DATABASE_URL"] = "sqlite:///file:memdb?mode=memory&cache=shared&uri=true"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_SERVICE_KEY"] = ""
os.environ["SUPABASE_DB_PASSWORD"] = ""


def pytest_configure(config):
    set_default_reporter(PythonNativeReporter())


def ensure_all_models_registered():
    """Import all SQLModel table models so they register with SQLModel.metadata.

    Tests that call SQLModel.metadata.create_all() need every model's table
    and its FK targets to be present in the metadata. Without this, models
    imported transitively (e.g. MatcherJob with FK to users) will fail with
    NoReferencedTableError because the target model was never imported.
    """
    import app.data.database.local.demo_match_repo  # noqa: F401
    import app.data.database.local.demo_match_task_repo  # noqa: F401
    import app.data.database.model.jobs  # noqa: F401
    import app.data.database.model.llm_provider_config  # noqa: F401
    import app.data.database.model.match_result  # noqa: F401
    import app.data.database.model.ocr_model  # noqa: F401
    import app.data.database.model.ocr_result  # noqa: F401
    import app.data.database.model.petition_crop  # noqa: F401
    import app.data.database.model.petition_scan  # noqa: F401
    import app.data.database.model.registered_voter  # noqa: F401
    import app.data.database.model.schema  # noqa: F401
    import app.data.database.model.user  # noqa: F401
    import app.data.database.model.voter_list_upload  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def _register_all_models():
    ensure_all_models_registered()
