"""Connectors Layer — integrations with external systems."""
from solar_core.connectors.base import BaseConnector, ConnectorAction, ConnectorResult
from solar_core.connectors.registry import ConnectorRegistry, get_connector_registry
from solar_core.connectors.solar_erp import SolarERPConnector
from solar_core.connectors.telegram import TelegramConnector

__all__ = [
    "BaseConnector",
    "ConnectorAction",
    "ConnectorRegistry",
    "ConnectorResult",
    "SolarERPConnector",
    "TelegramConnector",
    "get_connector_registry",
]
