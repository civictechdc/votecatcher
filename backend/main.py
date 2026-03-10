import argparse
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

	match env_selection:
		case EnvironmentSelection.LOCAL | EnvironmentSelection.DEBUG:
			env_path = Path(".env.local")
		case EnvironmentSelection.DEV:
			env_path = Path(".env.dev")
		case EnvironmentSelection.PRODUCTION:
			env_path = Path(".env.prod")
		case _:
			env_path = None

	uvicorn.run(
		app="app.api:app", host="0.0.0.0", port=8080, reload=True, env_file=env_path
	)
