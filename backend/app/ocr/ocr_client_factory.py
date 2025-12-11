import json
import os

from app.ocr.data.data_models import OCRData
from app.settings import GeminiAiConfig, MistralAiConfig, OpenAiConfig, load_settings
from app.settings.settings_repo import GeminiAiConfig, MistralAiConfig, OpenAiConfig
from app.utils.app_logger import logger
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI

load_dotenv()


TEXT_PROMPTS: list[str] = [
    """Using the written text in the image create a list of dictionaries where each dictionary consists of keys 'Name', 'Address', 'Date', and 'Ward'. Fill in the values of each dictionary with the correct entries for each key. Write all the values of the dictionary in full. Only output the list of dictionaries. No other intro text is necessary.""",
    """Remove the city name 'Washington, DC' and any zip codes from the 'Address' values.""",
]


def _create_ocr_client() -> Runnable:
    """
    Create an OpenAI client with the appropriate settings.

    Returns:
        Runnable: An AI client for OCR extraction.
    """

    env_provider = os.getenv("OCR_PROVIDER_NAME")
    enable_env_override = env_provider is not None and len(env_provider) > 0

    ocr_config = load_settings(enable_env_override=enable_env_override).selected_config
    client: Runnable | None = None

    match ocr_config:
        case OpenAiConfig():
            client = ChatOpenAI(
                api_key=ocr_config.api_key,
                temperature=1,
                openai_api_base="https://oai.helicone.ai/v1",
                model=ocr_config.model,
            ).with_structured_output(OCRData)
        case MistralAiConfig():
            client = ChatMistralAI(
                api_key=ocr_config.api_key,
                temperature=0.0,
                model_name=ocr_config.model,
            ).with_structured_output(OCRData)
        case GeminiAiConfig():
            client = ChatGoogleGenerativeAI(
                api_key=ocr_config.api_key,
                temperature=0.0,
                model=ocr_config.model,
            ).with_structured_output(OCRData)

    logger.debug(f"Creating client {ocr_config}")

    return client


async def perform_batch_extraction(base64_encoded_images: list[str]):
    if len(base64_encoded_images) == 0:
        raise ValueError("Please provide a list of encoded images to match")

    client = _create_ocr_client()
    inputs: list[HumanMessage] = []

    for img in base64_encoded_images:
        message = HumanMessage(
            content=[
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
            ]
        )

        inputs.append(message)

    job = await client.abatch(inputs=inputs)


async def extract_from_encoding_async(base64_image: str) -> list[dict]:
    """
    Extracts names and addresses from single ballot image asynchronously.
    Uses base64_image

    Args:
        base64_image: The base64 encoded image to extract data from.

    Returns:
        list: A list of dictionaries with the OCR data.
    """
    logger.debug("Starting OCR extraction for image")

    try:
        # AI client definition
        client = _create_ocr_client()
        # prompt message
        messages = [
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
                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
            },
        ]

        results = await client.ainvoke([HumanMessage(content=messages)])

        parsed_results = results

        # dictionary results
        parsed_list = json.loads(parsed_results.json())["Data"]
        logger.debug(f"Successfully extracted {len(parsed_list)} entries from image")
        return parsed_list

    except Exception as e:
        logger.error(f"Error in OCR extraction: {str(e)}")
        raise
