from app.matching.match_columns import MatchColumns
from app.schemas import MatchFieldsResponse
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
