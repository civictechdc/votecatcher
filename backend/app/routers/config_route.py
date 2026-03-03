from app.matching.match_columns import MatchColumns
from app.schemas import MatchFieldsResponse
from app.settings.env_settings import get_settings
from fastapi.routing import APIRouter

router: APIRouter = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("/match-fields/{id}")
async def fetch_match_columns(id: str) -> MatchFieldsResponse:

	# TODO: Handle different column configurations via settings or config
	match_columns: MatchColumns = MatchColumns()

	response: MatchFieldsResponse = MatchFieldsResponse(
		id=id, field_names=match_columns.COLUMNS()
	)

	return response


@router.get("/features")
async def get_feature_config():
	"""
	Get feature flag configuration.

	Returns server-side feature flags that can be overridden
	by client-side localStorage preferences.
	"""
	settings = get_settings()
	return {
		"simulationMode": settings.enable_simulation,
		"betaFeatures": settings.enable_beta_features,
		"debugMode": settings.enable_debug_mode,
	}
