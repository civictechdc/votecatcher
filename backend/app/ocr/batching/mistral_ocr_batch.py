import os
from pathlib import Path

from app.settings import MistralAiConfig
from mistralai import Mistral


def create_mistral_batch_job(
    config: MistralAiConfig, request_batch: list[Any], jsonl_path: Path
):
    client = Mistral(api_key=config.api_key)
    batch_data = client.files.upload(
        file={"file_name": "test.jsonl", "content": open("test.jsonl", "rb")},
        purpose="batch",
    )
