"""AI Orchestrator — high-level interface for AI completions.

Handles:
  - provider selection (via router)
  - retries with fallback to alternate provider
  - prompt templating
  - usage logging
"""
import time
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from solar_core.ai.providers import AICompletion, AIMessage
from solar_core.ai.router import AIRouter, TaskType
from solar_core.core.exceptions import AIProviderError
from solar_core.core.logging import get_logger

logger = get_logger(__name__)


class AIOrchestrator:
    """High-level AI orchestration."""

    def __init__(self, router: AIRouter | None = None):
        self.router = router or AIRouter()

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=True,
    )
    async def complete(
        self,
        messages: list[AIMessage],
        task: TaskType = "default",
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AICompletion:
        """Complete with primary provider; fallback to secondary on failure."""
        decision = self.router.route(task)
        start = time.perf_counter()

        try:
            result = await decision.provider.complete(
                messages=messages,
                model=decision.model,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "ai_completion_ok",
                provider=result.provider,
                model=result.model,
                task=task,
                duration_ms=int(elapsed),
                input_tokens=result.usage.get("input_tokens") if result.usage else None,
                output_tokens=result.usage.get("output_tokens") if result.usage else None,
            )
            return result
        except AIProviderError as e:
            logger.warning(
                "ai_completion_failed",
                provider=decision.provider.name,
                model=decision.model,
                task=task,
                error=str(e),
            )
            raise

    async def complete_text(
        self,
        prompt: str,
        system: str | None = None,
        task: TaskType = "default",
        **kwargs: Any,
    ) -> AICompletion:
        """Convenience: single-turn completion with optional system prompt."""
        messages: list[AIMessage] = []
        if system:
            messages.append(AIMessage(role="system", content=system))
        messages.append(AIMessage(role="user", content=prompt))
        return await self.complete(messages=messages, task=task, **kwargs)
