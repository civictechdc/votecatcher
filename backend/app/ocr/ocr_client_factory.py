import json
from dataclasses import dataclass
from typing import Any, List, override

from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.data.database.model.llm_provider_config import LlmProviderConfig
from app.settings import get_settings
from app.utils.app_logger import logger


@dataclass
class ProviderConfig:
    provider: str
    api_key: str
    model: str

    @override
    def __repr__(self) -> str:
        return (
            f"ProviderConfig(provider={self.provider!r},"
            f" api_key=***, model={self.model!r})"
        )


def resolve_provider_config(
    provider: str | None = None,
    session: Session | None = None,
) -> ProviderConfig:
    if session is not None:
        if provider is not None:
            db_config = session.exec(
                select(LlmProviderConfig).where(LlmProviderConfig.provider == provider)
            ).first()
        else:
            db_config = session.exec(
                select(LlmProviderConfig).where(
                    LlmProviderConfig.is_configured == True  # noqa: E712
                )
            ).first()

        if db_config and db_config.api_key and db_config.model:
            return ProviderConfig(
                provider=db_config.provider,
                api_key=db_config.api_key,
                model=db_config.model,
            )

    settings = get_settings()
    if settings.ocr.provider_name and settings.ocr.model and settings.ocr.api_key:
        return ProviderConfig(
            provider=settings.ocr.provider_name,
            api_key=settings.ocr.api_key.get_secret_value(),
            model=settings.ocr.model,
        )

    msg = (
        "No OCR provider configured. Configure via the settings UI or set "
        + "OCR_PROVIDER_NAME, OCR_PROVIDER_MODEL, and OCR_PROVIDER_API_KEY "
        + "environment variables."
    )
    raise ValueError(msg)


TEXT_PROMPTS: list[str] = [
    (
        "Using the written text in the image create a list of dictionaries where "
        "each dictionary consists of keys 'Name', 'Address', 'Date', and 'Ward'. "
        "Fill in the values of each dictionary with the correct entries for each "
        "key. Write all the values of the dictionary in full. Only output the list "
        "of dictionaries. No other intro text is necessary."
    ),
    ("Remove the city name 'Washington, DC' and any zip codes from the Address."),
]


###
## OCR FUNCTIONS
###
class OCREntry(BaseModel):
    """Ballot signatory data"""

    Name: str = Field(description="Name of the petition signer")
    Address: str = Field(description="Address of the petition signatory")
    Date: str = Field(description="Date of the signed")
    Ward: int = Field(description="The area or 'Ward' that the signer belongs to")


class OCRData(BaseModel):
    Data: List[OCREntry]


async def _extract_openai(
    config: ProviderConfig, base64_image: str
) -> list[dict[str, Any]]:
    from openai import AsyncOpenAI
    from openai.lib._pydantic import to_strict_json_schema
    from openai.types.chat import (
        ChatCompletionContentPartImageParam,
        ChatCompletionContentPartTextParam,
        ChatCompletionUserMessageParam,
    )

    client = AsyncOpenAI(
        api_key=config.api_key,
        base_url="https://oai.helicone.ai/v1",
    )

    message_parts: list[
        ChatCompletionContentPartTextParam | ChatCompletionContentPartImageParam
    ] = [
        ChatCompletionContentPartTextParam(type="text", text=TEXT_PROMPTS[0]),
        ChatCompletionContentPartTextParam(type="text", text=TEXT_PROMPTS[1]),
        ChatCompletionContentPartImageParam(
            type="image_url",
            image_url={"url": f"data:image/jpeg;base64,{base64_image}"},
        ),
    ]

    user_msg = ChatCompletionUserMessageParam(
        role="user",
        content=message_parts,
    )

    response = await client.chat.completions.create(
        model=config.model,
        temperature=1,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "OCRData",
                "schema": to_strict_json_schema(model=OCRData),
                "strict": True,
            },
        },
        messages=[user_msg],
    )

    content = response.choices[0].message.content
    if not content:
        return []

    parsed_data: dict[str, Any] = json.loads(content)
    return parsed_data.get("data", [])


async def _extract_gemini(
    config: ProviderConfig, base64_image: str
) -> list[dict[str, Any]]:
    import base64 as b64mod

    from google import genai
    from google.genai.types import GenerateContentConfig, Part

    client = genai.Client(api_key=config.api_key)

    image_bytes: bytes = b64mod.b64decode(base64_image)
    image_part = Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    response = await client.aio.models.generate_content(
        model=f"models/{config.model}",
        contents=[TEXT_PROMPTS[0], TEXT_PROMPTS[1], image_part],
        config=GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OCRData,
        ),
    )

    if not response.text:
        return []

    parsed_data: dict[str, Any] = json.loads(response.text)
    return parsed_data.get("data", [])


async def _extract_mistral(
    config: ProviderConfig, base64_image: str
) -> list[dict[str, Any]]:
    from mistralai.client import Mistral

    client = Mistral(api_key=config.api_key)

    image_url = f"data:image/jpeg;base64,{base64_image}"
    content_str = f"{TEXT_PROMPTS[0]}\n\n{TEXT_PROMPTS[1]}\n\n[image: {image_url}]"

    response = await client.chat.complete_async(
        model=config.model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": content_str}],
    )

    resp_content = response.choices[0].message.content
    if not resp_content or isinstance(resp_content, list):
        return []

    parsed_data: dict[str, Any] = json.loads(resp_content)
    return parsed_data.get("data", [])


_PROVIDER_EXTRACTORS: dict[str, Any] = {
    "openai": _extract_openai,
    "gemini": _extract_gemini,
    "mistral": _extract_mistral,
}


async def extract_from_encoding_async(
    base64_image: str,
    config: ProviderConfig | None = None,
) -> list[dict[str, Any]]:
    logger.debug("Starting OCR extraction for image")

    try:
        if config is None:
            config = resolve_provider_config()

        extractor = _PROVIDER_EXTRACTORS.get(config.provider)
        if extractor is None:
            raise ValueError(f"Unsupported OCR provider: {config.provider}")

        logger.debug(f"Extracting with provider {config}")

        parsed_list = await extractor(config, base64_image)
        logger.info(f"Successfully extracted {len(parsed_list)} entries from image")
        return parsed_list

    except Exception as e:
        logger.error(f"Error in OCR extraction: {str(e)}")
        raise
