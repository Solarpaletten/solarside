"""Base class for actions."""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from solar_core.ai import AIOrchestrator
from solar_core.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ActionContext:
    """Input to an action."""

    text: str
    url: str | None = None
    language: str = "en"
    extra: dict[str, Any] | None = None


@dataclass
class ActionResult:
    """Output from an action."""

    success: bool
    data: dict[str, Any]
    provider: str | None = None
    model: str | None = None
    duration_ms: int | None = None
    error: str | None = None


class BaseAction(ABC):
    """Base class for all actions."""

    name: str = "base"
    description: str = ""

    def __init__(self, ai: AIOrchestrator | None = None):
        self.ai = ai or AIOrchestrator()

    @abstractmethod
    async def execute(self, ctx: ActionContext) -> ActionResult:
        """Execute the action."""
        ...

    @staticmethod
    def _parse_json_response(text: str) -> dict[str, Any]:
        """Parse JSON, tolerating markdown code fences."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            # strip ```json ... ``` or ``` ... ```
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning("action_json_parse_failed", error=str(e), raw=text[:200])
            return {"raw": text, "parse_error": str(e)}
