from pathlib import Path
from typing import Any

from mistralai import Mistral

from app.settings import MistralAiConfig


def create_mistral_batch_job(
	config: MistralAiConfig, request_batch: list[Any], jsonl_path: Path
):
	client = Mistral(api_key=config.api_key)
	client.files.upload(
		file={"file_name": "test.jsonl", "content": open("test.jsonl", "rb")},
		purpose="batch",
	)
