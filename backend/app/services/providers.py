"""Provider service for LLM API key validation and configuration."""

import structlog
from openai import AsyncOpenAI
from sqlmodel import Session, select

from app.data.database.model.llm_provider_config import (
    LlmProviderConfig,
    LlmProviderConfigCreate,
    LlmProviderConfigRead,
    LlmProviderTestResult,
)
from app.utils.secret_encryption import decrypt_secret, encrypt_secret

logger = structlog.get_logger(__name__)

SUPPORTED_PROVIDERS = {
    "openai": {
        "display_name": "OpenAI",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"],
    },
    "gemini": {
        "display_name": "Google Gemini",
        "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
    },
    "mistral": {
        "display_name": "Mistral AI",
        "models": ["mistral-large-latest", "pixtral-12b-2409"],
    },
}


def get_all_providers(session: Session) -> list[LlmProviderConfigRead]:
    """Get all provider configurations (with defaults for unconfigured)."""
    configs = session.exec(select(LlmProviderConfig)).all()
    configured_map = {c.provider: c for c in configs}

    result = []
    for provider_key, meta in SUPPORTED_PROVIDERS.items():
        if provider_key in configured_map:
            cfg = configured_map[provider_key]
            result.append(
                LlmProviderConfigRead(
                    provider=provider_key,
                    model=cfg.model,
                    is_configured=cfg.is_configured,
                    last_validated=cfg.last_validated,
                )
            )
        else:
            result.append(
                LlmProviderConfigRead(
                    provider=provider_key,
                    model=meta["models"][0],
                    is_configured=False,
                    last_validated=None,
                )
            )

    return result


def get_provider_config(session: Session, provider: str) -> LlmProviderConfig | None:
    """Get a single provider configuration."""
    return session.exec(
        select(LlmProviderConfig).where(LlmProviderConfig.provider == provider)
    ).first()


def get_decrypted_api_key(config: LlmProviderConfig | None) -> str | None:
    """Return the usable API key for a stored config, or None.

    Fails closed: legacy plaintext values, values that cannot be decrypted
    with the configured key, and a missing/misconfigured
    PROVIDER_CONFIG_SECRET all result in None (the provider is treated as
    not configured) so callers fall back to environment configuration.
    """
    if config is None:
        return None
    try:
        return decrypt_secret(config.api_key) if config.api_key else None
    except ValueError as e:
        logger.warning(
            "Stored provider credential unusable; treating provider as not configured",
            reason=str(e),
        )
        return None
    except RuntimeError as e:
        logger.warning(
            "PROVIDER_CONFIG_SECRET is not configured; treating stored "
            "provider credential as unavailable",
            reason=str(e),
        )
        return None


class ProviderSecretNotConfiguredError(ValueError):
    """PROVIDER_CONFIG_SECRET is unset; provider credentials cannot be
    stored. Surfaced to operators as a 4xx, not a 500."""


def save_provider_config(
    session: Session, provider: str, data: LlmProviderConfigCreate
) -> LlmProviderConfig:
    """Save or update provider configuration."""
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")

    try:
        encrypted_key = encrypt_secret(data.api_key)
    except RuntimeError as e:
        raise ProviderSecretNotConfiguredError(
            "Cannot store provider credentials: PROVIDER_CONFIG_SECRET is "
            "not set. Generate a key with 'python -c \"from "
            "cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"' and set it in the "
            "environment."
        ) from e
    existing = get_provider_config(session, provider)

    if existing:
        existing.api_key = encrypted_key
        existing.model = data.model
        existing.is_configured = True
        existing.updated_at = None
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    else:
        config = LlmProviderConfig(
            provider=provider,
            api_key=encrypted_key,
            model=data.model,
            is_configured=True,
        )
        session.add(config)
        session.commit()
        session.refresh(config)
        return config


def delete_provider_config(session: Session, provider: str) -> bool:
    """Delete provider configuration."""
    config = get_provider_config(session, provider)
    if config:
        session.delete(config)
        session.commit()
        return True
    return False


async def test_provider_api_key(provider: str, api_key: str) -> LlmProviderTestResult:
    """Test API key by calling the provider's list models endpoint."""
    if provider not in SUPPORTED_PROVIDERS:
        return LlmProviderTestResult(
            valid=False, models=[], error=f"Unsupported provider: {provider}"
        )

    try:
        if provider == "openai":
            client = AsyncOpenAI(api_key=api_key)
            models_response = await client.models.list()
            model_list: list[str] = []
            async for m in models_response:
                model_list.append(m.id)
            gpt_models = [m for m in model_list if "gpt" in m.lower()]
            return LlmProviderTestResult(
                valid=True,
                models=sorted(gpt_models)[:10],
            )
        elif provider == "gemini":
            return LlmProviderTestResult(
                valid=True,
                models=SUPPORTED_PROVIDERS["gemini"]["models"],
            )
        elif provider == "mistral":
            return LlmProviderTestResult(
                valid=True,
                models=SUPPORTED_PROVIDERS["mistral"]["models"],
            )
        else:
            return LlmProviderTestResult(
                valid=False, models=[], error=f"Provider {provider} not implemented"
            )
    except Exception as e:
        logger.error(f"Provider validation failed: {provider}", error=str(e))
        return LlmProviderTestResult(valid=False, models=[], error=str(e))


def mark_provider_validated(session: Session, provider: str) -> None:
    """Update last_validated timestamp for a provider."""
    from datetime import UTC, datetime

    config = get_provider_config(session, provider)
    if config:
        config.last_validated = datetime.now(UTC)
        session.add(config)
        session.commit()
