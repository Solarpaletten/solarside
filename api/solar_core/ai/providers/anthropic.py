"""Anthropic Claude provider."""
from typing import Any

from anthropic import AsyncAnthropic

from solar_core.ai.providers.base import AICompletion, AIMessage, BaseAIProvider
from solar_core.config import get_ai_keys
from solar_core.core.exceptions import AIProviderError
from solar_core.core.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider."""

    name = "anthropic"
    default_model = "claude-sonnet-4-6"

    def __init__(self, api_key: str | None = None):
        keys = get_ai_keys()
        self.api_key = api_key or keys.anthropic_api_key
        self._client: AsyncAnthropic | None = None

    @property
    def client(self) -> AsyncAnthropic:
        if self._client is None:
            if not self.api_key:
                raise AIProviderError(
                    "Anthropic API key is not configured",
                    {"provider": "anthropic"},
                )
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def complete(
        self,
        messages: list[AIMessage],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AICompletion:
        """Call Anthropic Messages API."""
        model = model or self.default_model

        # Anthropic API: system message — отдельный параметр
        system_parts = [m.content for m in messages if m.role == "system"]
        system_prompt = "\n\n".join(system_parts) if system_parts else None

        api_messages = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]

        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=api_messages,
            )
        except Exception as e:
            logger.error("anthropic_completion_failed", error=str(e), model=model)
            raise AIProviderError(f"Anthropic API error: {e}", {"provider": "anthropic"}) from e

        text = "".join(
            block.text for block in response.content if hasattr(block, "text")
        )

        return AICompletion(
            text=text,
            provider=self.name,
            model=model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            raw=response,
        )
