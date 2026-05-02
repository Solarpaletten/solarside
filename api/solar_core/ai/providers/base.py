"""Abstract base class for AI providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIMessage:
    """A single message in a conversation."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class AICompletion:
    """Result of an AI completion."""

    text: str
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    raw: Any = None


class BaseAIProvider(ABC):
    """Base class for all AI providers."""

    name: str = "base"

    @abstractmethod
    async def complete(
        self,
        messages: list[AIMessage],
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AICompletion:
        """Generate a completion from the AI."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the provider is configured/available."""
        ...
