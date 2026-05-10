"""AI provider routing: select the right provider/model for a given task."""
from dataclasses import dataclass
from typing import Literal

from solar_core.ai.providers import (
    AnthropicProvider,
    BaseAIProvider,
    DeepSeekProvider,
    OpenAIProvider,
)
from solar_core.config import get_settings
from solar_core.core.exceptions import AIProviderError
from solar_core.core.logging import get_logger

logger = get_logger(__name__)

TaskType = Literal[
    "reasoning",
    "extraction",
    "translation",
    "translation_air",
    "summarization",
    "default",
]


@dataclass
class RoutingDecision:
    provider: BaseAIProvider
    model: str


class AIRouter:
    """Routes AI requests to the most appropriate provider and model.

    Strategy:
      - reasoning, complex actions → Anthropic Claude (Sonnet/Opus)
      - simple extraction, summarization → DeepSeek (cost-efficient) → Anthropic Haiku fallback
      - translation → Claude (best multi-language)
      - fallback chain: requested → default → fallback
    """

    def __init__(self):
        self.settings = get_settings()
        self._providers: dict[str, BaseAIProvider] = {}

    def _get_provider(self, name: str) -> BaseAIProvider:
        if name not in self._providers:
            if name == "anthropic":
                self._providers[name] = AnthropicProvider()
            elif name == "openai":
                self._providers[name] = OpenAIProvider()
            elif name == "deepseek":
                self._providers[name] = DeepSeekProvider()
            else:
                raise AIProviderError(f"Unknown provider: {name}")
        return self._providers[name]

    def route(self, task: TaskType = "default") -> RoutingDecision:
        """Select provider and model for the given task type."""
        # Priority list per task type
        candidates: list[tuple[str, str]] = []

        if task == "reasoning":
            candidates = [
                ("anthropic", self.settings.ai_reasoning_model),
                ("openai", "gpt-4o"),
            ]
        elif task in ("extraction", "summarization"):
            candidates = [
                ("anthropic", self.settings.ai_extraction_model),
                ("deepseek", "deepseek-chat"),
                ("openai", "gpt-4o-mini"),
            ]
        elif task == "translation":
            candidates = [
                ("anthropic", self.settings.ai_reasoning_model),
                ("openai", "gpt-4o"),
            ]
        elif task == "translation_air":
            # Fast lane for short selections (<120 chars).
            # Haiku is ~3-5x faster than Sonnet and quality is plenty for words/phrases.
            candidates = [
                ("anthropic", self.settings.ai_extraction_model),
                ("deepseek", "deepseek-chat"),
                ("openai", "gpt-4o-mini"),
            ]
        else:  # default
            candidates = [
                (self.settings.ai_default_provider, self.settings.ai_reasoning_model),
                (self.settings.ai_fallback_provider, "gpt-4o-mini"),
            ]

        # Pick the first available provider
        for provider_name, model in candidates:
            try:
                provider = self._get_provider(provider_name)
                if provider.is_available():
                    logger.debug(
                        "ai_router_selected",
                        task=task,
                        provider=provider_name,
                        model=model,
                    )
                    return RoutingDecision(provider=provider, model=model)
            except AIProviderError:
                continue

        raise AIProviderError(
            "No AI provider is available. Configure at least one API key.",
            {"task": task, "tried": [p[0] for p in candidates]},
        )
