"""Provider settings router for LLM configuration."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.data.database.model.llm_provider_config import (
    LlmProviderConfigCreate,
    LlmProviderConfigRead,
    LlmProviderTestResult,
)
from app.data.database.session import get_db_session
from app.services import providers as provider_service

router = APIRouter(prefix="/settings/providers", tags=["settings", "providers"])


@router.get("", response_model=list[LlmProviderConfigRead])
def list_providers(
    session: Annotated[Session, Depends(get_db_session)],
) -> list[LlmProviderConfigRead]:
    """Get all provider configurations."""
    return provider_service.get_all_providers(session)


@router.post("/{provider}", response_model=LlmProviderConfigRead)
def configure_provider(
    provider: str,
    data: LlmProviderConfigCreate,
    session: Annotated[Session, Depends(get_db_session)],
) -> LlmProviderConfigRead:
    """Save API key and model for a provider."""
    if provider not in provider_service.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}",
        )

    config = provider_service.save_provider_config(session, provider, data)
    return LlmProviderConfigRead(
        provider=config.provider,
        model=config.model,
        is_configured=config.is_configured,
        last_validated=config.last_validated,
    )


@router.post("/{provider}/test", response_model=LlmProviderTestResult)
async def test_provider(
    provider: str,
    data: LlmProviderConfigCreate,
    session: Annotated[Session, Depends(get_db_session)],
) -> LlmProviderTestResult:
    """Test provider API key by listing available models."""
    if provider not in provider_service.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}",
        )

    result = await provider_service.test_provider_api_key(provider, data.api_key)

    if result.valid:
        provider_service.mark_provider_validated(session, provider)

    return result


@router.delete("/{provider}")
def delete_provider(
    provider: str,
    session: Annotated[Session, Depends(get_db_session)],
) -> dict:
    """Delete provider configuration."""
    if provider not in provider_service.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}",
        )

    deleted = provider_service.delete_provider_config(session, provider)
    return {"success": deleted}
