"""Shared model import utility for database engines."""

# pyright: reportUnusedImport=false


def import_models() -> None:
	from app.data.database.model.jobs import (  # noqa: F401
		MatcherJob,
		OcrJob,
	)
	from app.data.database.model.llm_provider_config import (
		LlmProviderConfig,  # noqa: F401
	)
	from app.data.database.model.match_result import MatchResult  # noqa: F401
	from app.data.database.model.ocr_result import OcrResult  # noqa: F401
	from app.data.database.model.petition_crop import PetitionCrop  # noqa: F401
	from app.data.database.model.petition_scan import PetitionScan  # noqa: F401
	from app.data.database.model.registered_voter import (
		RegisteredVoter,  # noqa: F401
	)
	from app.data.database.model.schema import Campaign, Region  # noqa: F401
	from app.data.database.model.session import (
		Session as SessionModel,  # noqa: F401
	)
	from app.data.database.model.user import User  # noqa: F401
	from app.data.database.model.voter_list_upload import (
		VoterListUpload,  # noqa: F401
	)
