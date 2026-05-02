"""Health check endpoint."""
from fastapi import APIRouter

from solar_core import __version__
from solar_core.ai.providers import AnthropicProvider, DeepSeekProvider, OpenAIProvider
from solar_core.api.schemas import HealthResponse
from solar_core.config import get_settings

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Application health check."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        env=settings.env,
        ai_providers={
            "anthropic": AnthropicProvider().is_available(),
            "openai": OpenAIProvider().is_available(),
            "deepseek": DeepSeekProvider().is_available(),
        },
    )
