"""Registry for connectors."""
from solar_core.connectors.base import BaseConnector
from solar_core.connectors.solar_erp import SolarERPConnector
from solar_core.connectors.telegram import TelegramConnector
from solar_core.core.exceptions import ConnectorError


class ConnectorRegistry:
    """Singleton registry of connectors."""

    _instance: "ConnectorRegistry | None" = None

    def __new__(cls) -> "ConnectorRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connectors = {}
            cls._instance._register_builtins()
        return cls._instance

    def _register_builtins(self) -> None:
        self.register(SolarERPConnector())
        self.register(TelegramConnector())

    def register(self, connector: BaseConnector) -> None:
        self._connectors[connector.name] = connector

    def get(self, name: str) -> BaseConnector:
        if name not in self._connectors:
            raise ConnectorError(
                f"Unknown connector: {name}",
                {"available": list(self._connectors.keys())},
            )
        return self._connectors[name]

    def list_connectors(self) -> list[dict]:
        return [
            {
                "name": c.name,
                "description": c.description,
                "available": c.is_available(),
                "actions": [
                    {"name": a.name, "description": a.description}
                    for a in c.list_actions()
                ],
            }
            for c in self._connectors.values()
        ]


def get_connector_registry() -> ConnectorRegistry:
    return ConnectorRegistry()
