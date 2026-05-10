"""POST /v1/translate-air — fast lane for short/medium selections.

Differs from /v1/process:
  - No DB write (no Document, no Action record).
  - Routes to extraction_model (Haiku) instead of reasoning_model (Sonnet).
  - Tight max_tokens, low temperature.
  - Hard input-length cap (defensive).
  - Supports target_language="auto": Russian source → English, otherwise → Russian.

Designed for inline UI (Air bubble) where every 100ms matters.
"""
import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from solar_core.ai import AIOrchestrator
from solar_core.core.auth import verify_api_key
from solar_core.core.exceptions import ValidationError
from solar_core.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["translate-air"])

# Frontend caps at 1000 (full paragraph). Backend accepts up to 1200 for headroom.
MAX_AIR_INPUT_LENGTH = 1200

# ──────────── Prompts (inline — direct, force translation) ────────────

# Explicit-target prompt (when client sends "ru", "en", etc.)
SYSTEM_EXPLICIT = """You are a translator. You ALWAYS produce a translation.
You NEVER return the source text unchanged.
You NEVER add explanation, preamble, or quotes.
Output ONLY the translation."""

USER_EXPLICIT = """Translate the following text into {language_full} ({language_code}).

Even if the source is already in {language_full}, rephrase it idiomatically in {language_full}.

Source text:
{text}"""

# Auto-detect prompt (when client sends "auto")
SYSTEM_AUTO = """You are a translator. You ALWAYS produce a translation.
You NEVER return the source text unchanged.
You NEVER add explanation, preamble, or quotes.

Decide the target language by these rules:
- If the source text is in Russian → translate to English.
- Otherwise (English, Latvian, German, Lithuanian, Spanish, French, etc.) → translate to Russian.

Output ONLY the translation."""

USER_AUTO = """Translate the following text following the auto-detect rules.

Source text:
{text}"""

# ──────────── Language code → human name ────────────
LANG_NAMES = {
    "ru": "Russian",
    "en": "English",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "de": "German",
    "es": "Spanish",
    "fr": "French",
    "it": "Italian",
    "pl": "Polish",
    "uk": "Ukrainian",
    "be": "Belarusian",
    "et": "Estonian",
}


class TranslateAirRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Selected text to translate.")
    target_language: str = Field(
        default="auto",
        description="Target language ISO code, or 'auto' for smart detection.",
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
    """Inline translation for short/medium selections. No persistence, no metadata."""
    if len(req.text) > MAX_AIR_INPUT_LENGTH:
        raise ValidationError(
            f"Air translation expects text up to {MAX_AIR_INPUT_LENGTH} chars. "
            "Use /v1/process for longer texts.",
            {"length": len(req.text), "max": MAX_AIR_INPUT_LENGTH},
        )

    target = (req.target_language or "auto").lower().strip()
    is_auto = target == "auto"

    if is_auto:
        system = SYSTEM_AUTO
        prompt = USER_AUTO.format(text=req.text)
    else:
        language_full = LANG_NAMES.get(target, target.upper())
        system = SYSTEM_EXPLICIT
        prompt = USER_EXPLICIT.format(
            language_full=language_full,
            language_code=target,
            text=req.text,
        )

    logger.info(
        "translate_air_request",
        length=len(req.text),
        target_language=target,
        is_auto=is_auto,
        text_preview=req.text[:60],
    )

    start = time.perf_counter()

    ai = AIOrchestrator()
    completion = await ai.complete_text(
        prompt=prompt,
        system=system,
        task="translation_air",
        max_tokens=1024,
        temperature=0.1,
    )

    elapsed = int((time.perf_counter() - start) * 1000)
    translation = completion.text.strip()

    # Diagnostic: detect the obvious failure mode where model returns the source.
    is_identical = translation == req.text.strip()
    logger.info(
        "translate_air_ok",
        length=len(req.text),
        target_language=target,
        provider=completion.provider,
        model=completion.model,
        duration_ms=elapsed,
        result_length=len(translation),
        result_preview=translation[:60],
        echoed_source=is_identical,
    )

    return TranslateAirResponse(
        translation=translation,
        target_language=target,
        provider=completion.provider,
        model=completion.model,
        duration_ms=elapsed,
    )
