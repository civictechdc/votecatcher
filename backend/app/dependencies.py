from pathlib import Path

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearer(
    tokenUrl="/api/token", scheme_name="JWT", refreshUrl=""
)


demo_petition_path: Path = Path("temp")
