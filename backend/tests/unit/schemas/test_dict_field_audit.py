"""BDD contract tests: ApiModel subclasses must not use bare dict fields.

Pydantic's alias_generator only transforms model field names, NOT dict contents.
Any dict-typed field in an ApiModel subclass silently bypasses camelCase serialization,
returning snake_case keys in the JSON response.

This test suite enforces two behaviors:
  1. No ApiModel subclass may declare a dict-typed field (except allowlisted opaque data)
  2. Known response models with previously-dict fields must serialize nested data as camelCase
"""

import inspect


from app.api_models import ApiModel

ALLOWLISTED_DICT_FIELDS: set[str] = {
    "CreateSessionRequest.snapshot_data",
    "SessionResponse.snapshot_data",
    "OcrMatchResponse.stats",
    "OcrMatchResponse.results",
}


def _find_all_api_model_subclasses() -> list[type[ApiModel]]:
    """Walk all imported modules and collect ApiModel subclasses."""
    import importlib
    import pkgutil

    import app.routers as routers_pkg
    import app.schemas as schemas_pkg

    subclasses: list[type[ApiModel]] = []
    seen: set[str] = set()

    modules_to_scan = [schemas_pkg]
    for _importer, modname, _ispkg in pkgutil.iter_modules(
        routers_pkg.__path__, routers_pkg.__name__ + "."
    ):
        try:
            modules_to_scan.append(importlib.import_module(modname))
        except Exception:
            continue

    for mod in modules_to_scan:
        for _name, obj in inspect.getmembers(mod, inspect.isclass):
            if (
                issubclass(obj, ApiModel)
                and obj is not ApiModel
                and obj.__module__ == mod.__name__
                and obj.__qualname__ not in seen
            ):
                seen.add(obj.__qualname__)
                subclasses.append(obj)

    return subclasses


def _has_dict_annotation(annotations: dict) -> list[str]:
    """Return field names whose annotation is a bare dict or dict[...]."""
    import types

    dict_fields: list[str] = []
    for field_name, annotation in annotations.items():
        origin = getattr(annotation, "__origin__", None)
        if origin is dict or annotation is dict:
            dict_fields.append(field_name)
        elif isinstance(annotation, str) and "dict" in annotation:
            dict_fields.append(field_name)
        elif isinstance(annotation, types.UnionType) or hasattr(annotation, "__args__"):
            for arg in getattr(annotation, "__args__", []):
                arg_origin = getattr(arg, "__origin__", None)
                if arg_origin is dict or arg is dict:
                    dict_fields.append(field_name)
                    break
    return dict_fields


class TestNoDictFieldsInApiModels:
    """ApiModel subclasses must not declare dict-typed fields.

    dict fields bypass alias_generator, so nested snake_case keys
    leak into camelCase JSON responses.
    """

    def test_no_api_model_has_dict_fields(self):
        violations: list[str] = []
        for cls in _find_all_api_model_subclasses():
            annotations = getattr(cls, "__annotations__", {})
            dict_fields = _has_dict_annotation(annotations)
            for field_name in dict_fields:
                qualified = f"{cls.__qualname__}.{field_name}"
                if qualified not in ALLOWLISTED_DICT_FIELDS:
                    violations.append(qualified)
        assert violations == [], (
            f"Found dict-typed fields in ApiModel subclasses: {violations}. "
            f"Replace with typed ApiModel sub-models. "
            f"If the field contains opaque client data, add to ALLOWLISTED_DICT_FIELDS."
        )


class TestVoterListStatusResponseUploadSerialization:
    """VoterListStatusResponse.upload must serialize nested keys as camelCase."""

    def test_upload_nested_keys_are_camel_case(self):
        from app.routers.region_router import UploadDetail, VoterListStatusResponse

        resp = VoterListStatusResponse(
            exists=True,
            upload=UploadDetail(
                id="uuid-1",
                original_filename="voters.csv",
                file_size=1024,
                row_count=500,
                uploaded_at="2025-01-01T00:00:00",
                status="ACTIVE",
            ),
        )
        dumped = resp.model_dump(by_alias=True)
        assert "upload" in dumped

        upload_data = dumped["upload"]
        assert isinstance(upload_data, dict)
        assert "originalFilename" in upload_data, (
            "upload dict has snake_case key 'original_filename' — "
            "replace dict field with typed ApiModel sub-model"
        )
        assert "fileSize" in upload_data
        assert "rowCount" in upload_data
        assert "uploadedAt" in upload_data

    def test_upload_none_serializes_correctly(self):
        from app.routers.region_router import VoterListStatusResponse

        resp = VoterListStatusResponse(exists=False, upload=None)
        dumped = resp.model_dump(by_alias=True)
        assert dumped["upload"] is None


class TestCampaignMetricsResponseLastJobSerialization:
    """CampaignMetricsResponse.last_job must serialize nested keys as camelCase."""

    def test_last_job_nested_keys_are_camel_case(self):
        from app.routers.campaign_router import CampaignMetricsResponse, LastJobInfo

        resp = CampaignMetricsResponse(
            total_signatures=10,
            processed=5,
            high_confidence=3,
            medium_confidence=1,
            low_confidence=1,
            progress_percentage=50.0,
            last_job=LastJobInfo(
                id=1,
                status="MATCHING_COMPLETED",
                completed_at="2025-01-01T00:00:00",
            ),
            voter_list_count=100,
        )
        dumped = resp.model_dump(by_alias=True)
        assert dumped["lastJob"] is not None

        last_job_data = dumped["lastJob"]
        assert isinstance(last_job_data, dict)
        assert "completedAt" in last_job_data, (
            "lastJob dict has snake_case key 'completed_at' — "
            "replace dict field with typed ApiModel sub-model"
        )

    def test_last_job_none_serializes_correctly(self):
        from app.routers.campaign_router import CampaignMetricsResponse

        resp = CampaignMetricsResponse(
            total_signatures=0,
            processed=0,
            high_confidence=0,
            medium_confidence=0,
            low_confidence=0,
            progress_percentage=0.0,
            last_job=None,
            voter_list_count=None,
        )
        dumped = resp.model_dump(by_alias=True)
        assert dumped["lastJob"] is None


class TestResetDataResponseDeletedCountsSerialization:
    """ResetDataResponse.deleted_counts must serialize nested keys as camelCase."""

    def test_deleted_counts_nested_keys_are_camel_case(self):
        from app.routers.config_router import DeletedTableCounts, ResetDataResponse

        resp = ResetDataResponse(
            deleted_counts=DeletedTableCounts(
                match_results=5,
                ocr_results=10,
                ocr_jobs=2,
                matcher_jobs=1,
                petition_crops=3,
                petition_scans=1,
                campaigns=0,
            ),
            message="All data has been reset successfully",
        )
        dumped = resp.model_dump(by_alias=True)
        assert "deletedCounts" in dumped

        counts = dumped["deletedCounts"]
        assert isinstance(counts, dict)
        assert "matchResults" in counts, (
            "deletedCounts dict has snake_case key 'match_results' — "
            "replace dict field with typed ApiModel sub-model"
        )
        assert "ocrResults" in counts
        assert "ocrJobs" in counts
        assert "matcherJobs" in counts
        assert "petitionCrops" in counts
        assert "petitionScans" in counts
