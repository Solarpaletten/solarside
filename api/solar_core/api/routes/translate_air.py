"""POST /v1/translate-air — fast lane for short selections.

Differs from /v1/process:
  - No DB write (no Document, no Action record).
  - Routes to extraction_model (Haiku) instead of reasoning_model (Sonnet).
  - Tight max_tokens, low temperature.
  - Hard input-length cap (defensive).

Designed for inline UI (Air bubble) where every 100ms matters.
"""
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from solar_core.ai import AIOrchestrator
from solar_core.ai.prompts.builtin import TRANSLATE_AIR_SYSTEM, TRANSLATE_AIR_USER
from solar_core.core.auth import verify_api_key
from solar_core.core.exceptions import ValidationError
from solar_core.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["translate-air"])

# Defensive cap. Frontend should send <120 chars; we accept up to 500 to absorb
# slightly-longer pastes without rejecting the user.
MAX_AIR_INPUT_LENGTH = 500


class TranslateAirRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Selected text to translate.")
    target_language: str = Field(
        default="ru",
        description="Target language ISO code (en, ru, lt, lv, de, ...).",
    )


class TranslateAirResponse(BaseModel):
    translation: str
    target_language: str
    provider: str | None = None
    model: str | None = None
    duration_ms: int


@router.post(
    "/translate-air",
    response_model=TranslateAirResponse,
    dependencies=[Depends(verify_api_key)],
)
async def translate_air(req: TranslateAirRequest) -> TranslateAirResponse:
    """Inline translation for short selections. No persistence, no metadata."""
    if len(req.text) > MAX_AIR_INPUT_LENGTH:
        raise ValidationError(
            f"Air translation expects short text. Use /v1/process for >{MAX_AIR_INPUT_LENGTH} chars.",
            {"length": len(req.text), "max": MAX_AIR_INPUT_LENGTH},
        )

    start = time.perf_counter()

    ai = AIOrchestrator()
    prompt = TRANSLATE_AIR_USER.format(language=req.target_language, text=req.text)
    completion = await ai.complete_text(
        prompt=prompt,
        system=TRANSLATE_AIR_SYSTEM,
        task="translation_air",
        max_tokens=256,
        temperature=0.1,
    )

    elapsed = int((time.perf_counter() - start) * 1000)
    logger.info(
        "translate_air_ok",
        length=len(req.text),
        target_language=req.target_language,
        provider=completion.provider,
        model=completion.model,
        duration_ms=elapsed,
    )

    return TranslateAirResponse(
        translation=completion.text.strip(),
        target_language=req.target_language,
        provider=completion.provider,
        model=completion.model,
        duration_ms=elapsed,
    )
