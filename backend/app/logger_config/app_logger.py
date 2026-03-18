import logging
import os
import re
import sys
from collections.abc import Callable
from logging import Logger, StreamHandler
from logging.handlers import WatchedFileHandler
from pathlib import Path
from typing import Any, TextIO

import structlog
from asgi_correlation_id import correlation_id
from structlog.dev import ConsoleRenderer
from structlog.processors import (
	JSONRenderer,
)
from structlog.stdlib import ProcessorFormatter
from structlog.typing import Processor

SENSITIVE_FIELD_PATTERNS = [
	re.compile(r"api[_-]?key", re.IGNORECASE),
	re.compile(r"apikey", re.IGNORECASE),
	re.compile(r"secret", re.IGNORECASE),
	re.compile(r"password", re.IGNORECASE),
	re.compile(r"token", re.IGNORECASE),
	re.compile(r"credential", re.IGNORECASE),
]

API_KEY_VALUE_PATTERN = re.compile(r"^(sk-[a-zA-Z0-9_-]{10,}|[a-zA-Z0-9_-]{20,})$")


def redact_sensitive(value: Any, show_chars: int = 4) -> Any:
	if not isinstance(value, str) or len(value) < show_chars * 2:
		return value
	if API_KEY_VALUE_PATTERN.match(value):
		return f"{value[:show_chars]}***REDACTED***{value[-show_chars:]}"
	return value


def redact_api_keys(
	logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
	for key, value in list(event_dict.items()):
		key_lower = key.lower().replace("-", "_")
		for pattern in SENSITIVE_FIELD_PATTERNS:
			if pattern.search(key_lower):
				if isinstance(value, str):
					event_dict[key] = redact_sensitive(value)
				elif isinstance(value, dict):
					event_dict[key] = {
						k: redact_sensitive(v) if isinstance(v, str) else v
						for k, v in value.items()
					}
				break
		if isinstance(value, dict):
			for inner_key, inner_value in list(value.items()):
				inner_key_lower = inner_key.lower().replace("-", "_")
				for pattern in SENSITIVE_FIELD_PATTERNS:
					if pattern.search(inner_key_lower):
						if isinstance(inner_value, str):
							value[inner_key] = redact_sensitive(inner_value)
						break
	return event_dict


def add_correlation(
	logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
	"""Add request id to log message."""
	if request_id := correlation_id.get():
		event_dict["request_id"] = request_id
	return event_dict


def configure_logger(debug_enabled: bool = False) -> None:
	# https://gist.githubusercontent.com/Kludex/8e6d30de151f1d756c3c7364811c9429/raw/a6e8d5c0965b65623095781fb78d7499be357840/main.py
	shared_processors: list[Processor] = [
		structlog.contextvars.merge_contextvars,
		redact_api_keys,
		structlog.stdlib.add_log_level,
		structlog.processors.StackInfoRenderer(),
		structlog.processors.CallsiteParameterAdder(
			{
				structlog.processors.CallsiteParameter.FILENAME,
				structlog.processors.CallsiteParameter.LINENO,
			}
		),
		structlog.processors.TimeStamper(fmt="iso"),
	]

	structlog_processors: list[Processor] = shared_processors + []
	# Remove _record & _from_structlog.
	logging_processors: list[Processor] = [ProcessorFormatter.remove_processors_meta]

	if sys.stderr.isatty() or debug_enabled:
		console_renderer: ConsoleRenderer = structlog.dev.ConsoleRenderer()
		logging_processors.append(console_renderer)
		structlog_processors.append(console_renderer)
	else:
		json_renderer: JSONRenderer = structlog.processors.JSONRenderer(
			indent=1, sort_keys=True
		)
		structlog_processors.append(json_renderer)
		logging_processors.append(json_renderer)

	structlog.configure(
		processors=structlog_processors,
		wrapper_class=structlog.stdlib.BoundLogger,
		# logger_factory=structlog.stdlib.LoggerFactory(),
		logger_factory=structlog.PrintLoggerFactory(sys.stderr),
		context_class=dict,
		cache_logger_on_first_use=True,
	)

	formatter: ProcessorFormatter = ProcessorFormatter(
		# These run ONLY on `logging` entries that do NOT originate within
		# structlog.
		foreign_pre_chain=shared_processors,
		# These run on ALL entries after the pre_chain is done.
		processors=logging_processors,
	)

	handler: StreamHandler[TextIO | Any] = logging.StreamHandler(sys.stderr)
	# Use OUR `ProcessorFormatter` to format all `logging` entries.
	handler.setFormatter(formatter)
	logging.basicConfig(handlers=[handler], level=logging.INFO)

	logger: Logger = logging.getLogger("uvicorn.error")
	logger.handlers = [handler]
	logger.propagate = False


def configure_dev_logging() -> None:
	structlog.configure(
		wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
		processors=[
			structlog.contextvars.merge_contextvars,
			redact_api_keys,
			structlog.processors.add_log_level,
			structlog.processors.StackInfoRenderer(),
			structlog.dev.set_exc_info,
			structlog.processors.TimeStamper(fmt="iso"),
			structlog.dev.ConsoleRenderer(),
		],
	)


def configure_prod_logging() -> None:
	structlog.configure(
		wrapper_class=structlog.make_filtering_bound_logger(logging.WARNING),
		processors=[
			structlog.contextvars.merge_contextvars,
			redact_api_keys,
			structlog.processors.add_log_level,
			structlog.processors.StackInfoRenderer(),
			structlog.dev.set_exc_info,
			structlog.processors.dict_tracebacks,
			structlog.processors.TimeStamper(fmt="iso"),
			structlog.processors.JSONRenderer(),
		],
		context_class=dict,
		logger_factory=structlog.PrintLoggerFactory(),
		cache_logger_on_first_use=True,
	)


class AppLogger:
	def __init__(
		self,
		log_name: str,
		log_file_path: str | Path | None = None,
		min_log_level: int | None = None,
		timestamp_format: str | None = "iso",
	) -> None:
		# define basic configuration

		shared_processors: list[Callable[..., dict[str, Any]] | Processor] = [
			add_correlation,
			redact_api_keys,
			structlog.stdlib.filter_by_level,
			structlog.stdlib.add_log_level,
			structlog.stdlib.add_logger_name,
			structlog.stdlib.PositionalArgumentsFormatter(),
			structlog.processors.TimeStamper(fmt=timestamp_format),
			structlog.processors.StackInfoRenderer(),
			# structlog.processors.format_exc_info,
			structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
		]

		structlog.configure(
			processors=shared_processors,
			logger_factory=structlog.stdlib.LoggerFactory(),
			wrapper_class=structlog.stdlib.BoundLogger,
			cache_logger_on_first_use=True,
		)

		structlog.stdlib.ProcessorFormatter(
			# These run ONLY on `logging` entries that do NOT originate within
			# structlog.
			foreign_pre_chain=shared_processors,
			# These run on ALL entries after the pre_chain is done.
			processors=shared_processors
			+ [
				# Remove _record & _from_structlog.
				structlog.stdlib.ProcessorFormatter.remove_processors_meta,
			],
		)

		# define stdout handler
		console_handler: StreamHandler[TextIO | Any] = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(
			structlog.stdlib.ProcessorFormatter(
				# processor=structlog.dev.ConsoleRenderer(colors=True),
				# These run ONLY on `logging` entries that do NOT originate within
				# structlog.
				foreign_pre_chain=shared_processors,
				# These run on ALL entries after the pre_chain is done.
				processors=shared_processors
				+ [
					# Remove _record & _from_structlog.
					structlog.stdlib.ProcessorFormatter.remove_processors_meta,
					structlog.dev.ConsoleRenderer(colors=True),
				],
			),
		)

		# add handlers to single root logger
		root_logger = structlog.getLogger(log_name)
		root_logger.addHandler(console_handler)

		if log_file_path:
			file_path: Path = Path("logs").joinpath(log_file_path)
			if not os.path.exists(file_path.parent):
				os.makedirs(file_path.parent)
			# define log file handler
			file_handler: WatchedFileHandler = WatchedFileHandler(
				filename=Path("logs").joinpath(log_file_path), mode="wt"
			)
			file_handler.setFormatter(
				structlog.stdlib.ProcessorFormatter(
					processor=structlog.processors.JSONRenderer()
				)
			)

			root_logger.addHandler(file_handler)

		if min_log_level:
			# set logging level
			root_logger.setLevel(min_log_level)

		# Ensure we override the unvicorn logger
		for _log in ["uvicorn", "uvicorn.error"]:
			# Make sure the logs are handled by the root logger
			logging.getLogger(_log).handlers.clear()
			logging.getLogger(_log).propagate = True

			# Uvicorn logs re-emitted with more context; silence them here
			logging.getLogger("uvicorn.access").handlers.clear()
			logging.getLogger("uvicorn.access").propagate = False

		# add logger to class instance
		self.logger = root_logger

	@classmethod
	def get_logger(
		cls,
		log_name,
		log_file: Path | str | None = None,
		level: int | None = None,
		timestamp_format: str | None = None,
	):
		return cls(log_name, log_file, level, timestamp_format).logger
