from collections.abc import Generator
from pathlib import Path

import structlog
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.data.database.session import engine

load_dotenv()

logger = structlog.get_logger(__name__)

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
	tokenUrl="/api/token", scheme_name="JWT", refreshUrl=""
)

demo_petition_path: Path = Path("temp")


def get_session() -> Generator[Session]:
	"""Get database session for API endpoints."""
	with Session(engine) as session:
		yield session
