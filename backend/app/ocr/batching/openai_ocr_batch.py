import json
from pathlib import Path
from typing import Any

from app.ocr.ocr_client_factory import OpenAiConfig
from openai import OpenAI
from openai.types.batch import Batch


def _create_jsonl(req_contents: list[Any], parent_folder: Path) -> Path:
    file_path = parent_folder.joinpath("match_batch.jsonl")
    with open(file_path, "w") as file:
        for obj in req_contents:
            file.write(json.dumps(obj) + "\n")

    return file_path


def create_openai_batch_job(
    config: OpenAiConfig, request_batch: list[Any], jsonl_path: Path
) -> Batch:
    client = OpenAI(api_key=config.api_key)

    req_contents: list[Any] = []
    for idx, request in enumerate(request_batch):
        req_contents.append(
            {
                "custom_id": f"task-{idx + 1}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    # This is what you would have in your Chat Completions API call
                    "model": config.model,
                    "temperature": 0.2,
                    "max_tokens": 300,
                    "messages": [
                        # Add system prompt?
                        {
                            "role": "user",
                            "content": request,
                        }
                    ],
                },
            }
        )

    jsonl = _create_jsonl(req_contents, jsonl_path)
    batch_file = client.files.create(file=open(jsonl, "rb"), purpose="batch")

    batch: Batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    print(f"Created batch job: {batch.id}")
    return batch
