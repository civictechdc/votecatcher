"""Response contracts remain shared while router imports stay stable."""


def test_job_response_models_are_reexported_by_router():
    from app.responses.jobs import JobListResponse, JobResponse
    from app.routers.job_router import (
        JobListResponse as RouterJobListResponse,
    )
    from app.routers.job_router import JobResponse as RouterJobResponse

    assert RouterJobResponse is JobResponse
    assert RouterJobListResponse is JobListResponse
    assert tuple(JobResponse.model_fields) == (
        "job_id",
        "status",
        "campaign_id",
        "campaign_name",
        "provider_name",
        "provider_model",
        "force_reprocess",
        "cached_ocr_count",
        "new_ocr_count",
        "ocr_duration_seconds",
        "matching_duration_seconds",
        "created_at",
        "updated_at",
        "started_at",
        "ended_at",
        "error_message",
        "is_orphaned",
    )
    assert tuple(JobListResponse.model_fields) == ("jobs", "total")
    assert JobResponse.model_fields["force_reprocess"].default is False
    assert JobResponse.model_fields["is_orphaned"].default is False
    assert JobListResponse.model_fields["jobs"].annotation == list[JobResponse]
    assert tuple(JobResponse.model_json_schema(by_alias=True)["properties"]) == (
        "jobId",
        "status",
        "campaignId",
        "campaignName",
        "providerName",
        "providerModel",
        "forceReprocess",
        "cachedOcrCount",
        "newOcrCount",
        "ocrDurationSeconds",
        "matchingDurationSeconds",
        "createdAt",
        "updatedAt",
        "startedAt",
        "endedAt",
        "errorMessage",
        "isOrphaned",
    )


def test_results_response_models_are_reexported_by_router():
    from app.responses.results import (
        MatchPrediction,
        ResultResponse,
        ResultsListResponse,
    )
    from app.routers.results_router import (
        MatchPrediction as RouterMatchPrediction,
    )
    from app.routers.results_router import ResultResponse as RouterResultResponse
    from app.routers.results_router import (
        ResultsListResponse as RouterResultsListResponse,
    )

    assert RouterMatchPrediction is MatchPrediction
    assert RouterResultResponse is ResultResponse
    assert RouterResultsListResponse is ResultsListResponse
    assert tuple(MatchPrediction.model_fields) == (
        "rank",
        "voter_name",
        "voter_address",
        "similarity_score",
        "confidence",
    )
    assert tuple(ResultResponse.model_fields) == (
        "ocr_result_id",
        "extracted_text",
        "crop_id",
        "thumbnail_url",
        "predictions",
        "crop_coordinates",
        "entry_coordinates",
        "page_number",
        "document_name",
        "scan_id",
    )
    assert tuple(ResultsListResponse.model_fields) == (
        "results",
        "total",
        "page_size",
        "next_cursor",
    )
    assert ResultResponse.model_fields["document_name"].default == ""
    assert ResultsListResponse.model_fields["next_cursor"].default is None
    assert (
        ResultResponse.model_fields["predictions"].annotation == list[MatchPrediction]
    )
    assert tuple(MatchPrediction.model_json_schema(by_alias=True)["properties"]) == (
        "rank",
        "voterName",
        "voterAddress",
        "similarityScore",
        "confidence",
    )
    assert tuple(ResultResponse.model_json_schema(by_alias=True)["properties"]) == (
        "ocrResultId",
        "extractedText",
        "cropId",
        "thumbnailUrl",
        "predictions",
        "cropCoordinates",
        "entryCoordinates",
        "pageNumber",
        "documentName",
        "scanId",
    )
    assert tuple(
        ResultsListResponse.model_json_schema(by_alias=True)["properties"]
    ) == (
        "results",
        "total",
        "pageSize",
        "nextCursor",
    )
