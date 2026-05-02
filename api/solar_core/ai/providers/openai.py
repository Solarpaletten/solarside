"""OpenAI provider (fallback). Also works for DeepSeek (OpenAI-compatible API)."""
from typing import Any

from openai import AsyncOpenAI

from solar_core.ai.providers.base import AICompletion, AIMessage, BaseAIProvider
from solar_core.config import get_ai_keys
from solar_core.core.exceptions import AIProviderError
from solar_core.core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider. Used as fallback if Anthropic is unavailable."""

    name = "openai"
    default_model = "gpt-4o-mini"

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        keys = get_ai_keys()
        self.api_key = api_key or keys.openai_api_key
        self.base_url = base_url
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            if not self.api_key:
                raise AIProviderError(
                    "OpenAI API key is not configured",
                    {"provider": "openai"},
                )
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
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
        """Call OpenAI Chat Completions API."""
        model = model or self.default_model

        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response = await self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=api_messages,
            )
        except Exception as e:
            logger.error("openai_completion_failed", error=str(e), model=model)
            raise AIProviderError(f"OpenAI API error: {e}", {"provider": "openai"}) from e

        text = response.choices[0].message.content or ""

        return AICompletion(
            text=text,
            provider=self.name,
            model=model,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            raw=response,
        )


class DeepSeekProvider(OpenAIProvider):
    """DeepSeek provider — OpenAI-compatible API at deepseek.com.

    Cost-efficient for extraction / summarization.
    """

    name = "deepseek"
    default_model = "deepseek-chat"

    def __init__(self):
        keys = get_ai_keys()
        super().__init__(
            api_key=keys.deepseek_api_key,
            base_url="https://api.deepseek.com/v1",
        )
