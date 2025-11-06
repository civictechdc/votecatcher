from typing import Any

from app.settings.settings_repo import GeminiAiConfig
from google import genai
from google.genai import types
from google.genai.types import BatchJob


def create_gemini_batch_job(
    config: GeminiAiConfig, request_batch: list[Any]
) -> BatchJob:
    client = genai.Client(api_key=config.api_key)

    req_contents: list[Any] = []
    for request in request_batch:
        req_contents.append(
            {
                "contents": request,
            }
        )

    inline_batch_job: BatchJob = client.batches.create(
        model=f"models/{config.model}",
        src=req_contents,
        config={
            "display_name": "inlined-requests-job-1",
        },
    )

    print(f"Created batch job: {inline_batch_job.name}")
    return inline_batch_job
