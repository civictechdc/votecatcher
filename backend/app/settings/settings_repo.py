import os
import pathlib
import tomllib
from dataclasses import dataclass
from typing import override

from app.utils import enable_debug_logging, logger

config = {"BASE_THRESHOLD": 85, "TOP_CROP": 0.385, "BOTTOM_CROP": 0.725}


@dataclass
class OpenAiConfig:
	api_key: str
	model: str
	name: str = "open_ai"

	@override
	def __repr__(self) -> str:
		return f"OpenAiConfig(api_key=***, model={self.model!r}, name={self.name!r})"


@dataclass
class MistralAiConfig:
	api_key: str
	model: str
	name: str = "mistral_ai"

	@override
	def __repr__(self) -> str:
		return f"MistralAiConfig(api_key=***, model={self.model!r}, name={self.name!r})"


@dataclass
class GeminiAiConfig:
	api_key: str
	model: str
	name: str = "gemini_ai"

	@override
	def __repr__(self) -> str:
		return f"GeminiAiConfig(api_key=***, model={self.model!r}, name={self.name!r})"


@dataclass
class SettingsData:
	selected_config: OpenAiConfig | MistralAiConfig | GeminiAiConfig
	debug_mode: bool = False


_current_settings: SettingsData | None = None


def _create_provider_config(
	provider_name: str, provider_model: str, api_key: str
) -> OpenAiConfig | MistralAiConfig | GeminiAiConfig:
	match provider_name:
		case "open_ai":
			return OpenAiConfig(api_key=api_key, model=provider_model)
		case "gemini_ai":
			return GeminiAiConfig(api_key=api_key, model=provider_model)
		case "mistral_ai":
			return MistralAiConfig(api_key=api_key, model=provider_model)
		case _:
			raise ValueError(
				f"Could not find configuration for {provider_name}. Please try another."
			)


def override_settings(config: OpenAiConfig | MistralAiConfig | GeminiAiConfig):
	global _current_settings
	_current_settings = SettingsData(selected_config=config)


def load_settings(
	custom_path: str | None = None,
	reload_settings: bool = False,
	enable_env_override: bool = False,
) -> SettingsData:
	"""
	Load settings from a TOML file and return the selected OCR engine configuration.

	Args:
	    custom_path (str): Path to the TOML file. Defaults to "settings.toml"
	        if not provided.

	Returns:
	    SettingsData: Container for application including the selected OCR
	        engine configuration.

	Raises:
	    ValueError: If the selected engine is not found in the settings file.
	"""

	# If settings are already loaded and reload is not requested, return the
	# current settings

	# Load selected provider settings if the env variables are set
	if enable_env_override:
		env_provider_name: str | None = os.getenv("OCR_PROVIDER_NAME")
		env_provider_model: str | None = os.getenv("OCR_PROVIDER_MODEL")
		env_provider_api_key: str | None = os.getenv("OCR_PROVIDER_API_KEY")
		_current_settings = SettingsData(
			selected_config=_create_provider_config(
				env_provider_name, env_provider_model, env_provider_api_key
			)
		)
		logger.debug("Loading env settings override", settings=_current_settings)
		return _current_settings

	if (_current_settings) and (not reload_settings):
		return _current_settings

	# If custom path is provided, use it
	path = "./settings.toml"
	if custom_path:
		path = custom_path

	file = pathlib.Path(path)

	try:
		with open(file, "rb") as f:
			settings = tomllib.load(f)
	except (FileNotFoundError, tomllib.TOMLDecodeError):
		logger.info(
			f"Could not load settings from {file}. Please ensure the file "
			f"exists and is in the correct format."
		)
		settings = {
			"selected_ocr_engine": "open_ai",
			"open_ai": {"api_key": os.getenv("OPENAI_API_KEY"), "model": "gpt-4o"},
			"debug_mode": False,
		}

	selected_engine = settings["selected_ocr_engine"]
	engine_config = settings.get(selected_engine)
	is_debug_mode = settings.get("debug_mode", False)
	enable_debug_logging(is_debug_mode)

	match selected_engine:
		case "open_ai":
			_current_settings = SettingsData(
				selected_config=OpenAiConfig(
					api_key=engine_config["api_key"],
					model=engine_config["model"],
				)
			)
		case "mistral_ai":
			_current_settings = SettingsData(
				selected_config=MistralAiConfig(
					api_key=engine_config["api_key"],
					model=engine_config["model"],
				)
			)
		case "gemini_ai":
			_current_settings = SettingsData(
				selected_config=GeminiAiConfig(
					api_key=engine_config["api_key"],
					model=engine_config["model"],
				)
			)
		case _:
			raise ValueError(
				f"Could not find configuration for {selected_engine}. Please "
				f"check your settings file."
			)

	_current_settings.debug_mode = settings.get("debug_mode", False)

	logger.debug("Loaded settings", settings=_current_settings)
	logger.info(
		"Selected OCR engine {x} with model {y}:".format(
			x=selected_engine, y=engine_config["model"]
		)
	)

	return _current_settings
