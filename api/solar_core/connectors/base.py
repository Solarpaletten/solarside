"""Base class for connectors."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectorAction:
    """Description of an action a connector can perform."""

    name: str
    description: str
    params_schema: dict[str, Any]


@dataclass
class ConnectorResult:
    """Result of a connector action."""

    success: bool
    data: dict[str, Any]
    error: str | None = None


class BaseConnector(ABC):
    """Base class for all connectors (Solar ERP, Gmail, Google Docs, ...)."""

    name: str = "base"
    description: str = ""

    @abstractmethod
    async def execute(self, action: str, payload: dict[str, Any]) -> ConnectorResult:
        """Execute a named action against the connector."""
        ...

    @abstractmethod
    def list_actions(self) -> list[ConnectorAction]:
        """Return the list of supported actions."""
        ...

    def is_available(self) -> bool:
        """Whether this connector is configured and ready."""
        return True
