import argparse
import os
from argparse import ArgumentParser, Namespace
from enum import StrEnum
from pathlib import Path

import uvicorn


class EnvironmentSelection(StrEnum):
	LOCAL = "local"
	DEBUG = "debug"
	PRODUCTION = "prod"
	DEV = "dev"
	NONE = "None"


def _create_arg_parser() -> Namespace:
	parser: ArgumentParser = argparse.ArgumentParser(
		description="Process some integers."
	)
	_ = parser.add_argument(
		"--env",
		choices=[
			selection.value
			for selection in list[EnvironmentSelection](EnvironmentSelection)
		],
		default=EnvironmentSelection.NONE,
		help="Select the environment to run the backend.",
	)

	return parser.parse_args()


if __name__ == "__main__":
	args: Namespace = _create_arg_parser()
	env_selection: EnvironmentSelection = args.env
	env_path: Path | None = None
	env_filename: str | None = None

	match env_selection:
		case EnvironmentSelection.LOCAL | EnvironmentSelection.DEBUG:
			env_filename = ".env.local"
			env_path = Path(".env.local")
		case EnvironmentSelection.DEV:
			env_filename = ".env.dev"
			env_path = Path(".env.dev")
		case EnvironmentSelection.PRODUCTION:
			env_filename = ".env.prod"
			env_path = Path(".env.prod")
		case _:
			env_filename = ".env.local"
			env_path = None

	if env_filename:
		os.environ["ENV_FILE"] = env_filename

	uvicorn.run(
		app="app.api:app",
		host="0.0.0.0",  # nosec B104  # Development server, binding to all interfaces
		port=8080,
		reload=True,
		env_file=env_path,
	)
