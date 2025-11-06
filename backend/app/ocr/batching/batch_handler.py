import shutil
from pathlib import Path
from typing import Any

from app.ocr.batching.gemini_ocr_batch import create_gemini_batch_job
from app.ocr.batching.openai_ocr_batch import create_openai_batch_job
from app.ocr.ocr_client_factory import TEXT_PROMPTS
from app.settings import GeminiAiConfig, MistralAiConfig, OpenAiConfig

BATCH_JSONL_FOLDER = Path("batch")


def create_batch_payload(
    config: OpenAiConfig | GeminiAiConfig | MistralAiConfig, encoded_images: list[str]
):
    content_batch = []
    for img in encoded_images:

        content = {
            "parts": [
                {
                    "type": "text",
                    "text": TEXT_PROMPTS[0],
                },
                {
                    "type": "text",
                    "text": TEXT_PROMPTS[1],
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img}"},
                },
            ],
            "role": "user",
        }

        content_batch.append(content)

    if not BATCH_JSONL_FOLDER.exists():
        BATCH_JSONL_FOLDER.mkdir()

    shutil.rmtree(BATCH_JSONL_FOLDER)

    match config:
        case GeminiAiConfig():
            _ = create_gemini_batch_job(config=config, request_batch=content_batch)
        case OpenAiConfig():
            create_openai_batch_job(
                config=config,
                request_batch=content_batch,
                jsonl_path=BATCH_JSONL_FOLDER,
            )
        case _:
            pass
