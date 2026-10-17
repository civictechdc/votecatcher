"""CORS configuration builder.

Environment-aware CORS: strict origins in production, relaxed in development.
Production is fail-closed: a missing or empty CORS_ORIGINS raises at startup.
"""

_DEV_ORIGINS = ["http://localhost", "http://localhost:5173"]
_EXPLICIT_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
_PRODUCTION_HEADERS = ["Authorization", "Content-Type", "X-API-Key"]


def build_cors_config(
    environment: str, cors_origins: str
) -> dict[str, list[str] | bool]:
    is_production = environment == "production"

    if is_production:
        origins = _parse_origins(cors_origins)
        if not origins:
            raise ValueError(
                "CORS_ORIGINS is missing or empty in production. "
                "Set the CORS_ORIGINS environment variable to a comma-separated "
                "list of allowed origins, e.g. https://app.example.com."
            )
        if "*" in origins:
            raise ValueError(
                "CORS_ORIGINS must not contain a wildcard (*) in production. "
                "Wildcard origins are incompatible with credentialed CORS; "
                "list explicit origins instead."
            )
        return {
            "allow_origins": origins,
            "allow_methods": list(_EXPLICIT_METHODS),
            "allow_headers": list(_PRODUCTION_HEADERS),
            "allow_credentials": True,
        }

    return {
        "allow_origins": list(_DEV_ORIGINS),
        "allow_methods": list(_EXPLICIT_METHODS),
        "allow_headers": ["*"],
        "allow_credentials": True,
    }


def _parse_origins(raw: str) -> list[str]:
    if not raw:
        return []
    parts = [p.strip().rstrip("/") for p in raw.split(",")]
    return [p for p in parts if p]
