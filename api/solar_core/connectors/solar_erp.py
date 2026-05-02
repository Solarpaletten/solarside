"""Solar ERP connector — the flagship connector for Solar Core.

Currently a MOCK. Phase 1 / Step 2 will replace with real HTTP calls
to the SOLAR ERP backend (Prisma-based, port to be confirmed).

Supported actions (mock):
  - create_invoice       (Melasa Rail / Vagonupaletas / SOLARPALETTEN / YPL)
  - create_cmr           (logistics document for international transport)
  - create_note          (generic note attached to any entity)
  - lookup_counterparty  (find counterparty by name/VAT/address)
"""
import secrets
from typing import Any

from solar_core.config import get_settings
from solar_core.connectors.base import BaseConnector, ConnectorAction, ConnectorResult
from solar_core.core.logging import get_logger

logger = get_logger(__name__)


class SolarERPConnector(BaseConnector):
    """Connector to SOLAR ERP system (currently mocked)."""

    name = "solar_erp"
    description = "Solar ERP — invoices, CMR, customs, notes for the Solar group of companies."

    def __init__(self):
        self.settings = get_settings()

    def is_available(self) -> bool:
        # In Phase 1 we always return True — real availability check in Step 2.
        return True

    def list_actions(self) -> list[ConnectorAction]:
        return [
            ConnectorAction(
                name="create_invoice",
                description="Create an invoice in Solar ERP for a given entity.",
                params_schema={
                    "entity": "string (Melasa Rail | Vagonupaletas | SOLARPALETTEN | YPL)",
                    "counterparty": "string",
                    "amount": "number",
                    "currency": "string (EUR | USD)",
                    "items": "array",
                },
            ),
            ConnectorAction(
                name="create_cmr",
                description="Create a CMR international transport document.",
                params_schema={
                    "sender": "string",
                    "consignee": "string",
                    "goods": "string",
                    "weight_kg": "number",
                    "from_country": "string",
                    "to_country": "string",
                },
            ),
            ConnectorAction(
                name="create_note",
                description="Create a free-form note attached to an entity.",
                params_schema={
                    "entity": "string",
                    "title": "string",
                    "body": "string",
                    "tags": "array",
                },
            ),
            ConnectorAction(
                name="lookup_counterparty",
                description="Look up a counterparty by name, VAT, or address.",
                params_schema={
                    "query": "string",
                },
            ),
        ]

    async def execute(self, action: str, payload: dict[str, Any]) -> ConnectorResult:
        """Mock execute: log and return a synthetic ID."""
        logger.info("solar_erp_mock_execute", action=action, payload=payload)

        if action == "create_invoice":
            return ConnectorResult(
                success=True,
                data={
                    "invoice_id": f"INV-MOCK-{secrets.token_hex(4).upper()}",
                    "entity": payload.get("entity"),
                    "status": "draft",
                    "note": "MOCK — real ERP integration in Phase 1 / Step 2.",
                },
            )

        if action == "create_cmr":
            return ConnectorResult(
                success=True,
                data={
                    "cmr_id": f"CMR-MOCK-{secrets.token_hex(4).upper()}",
                    "status": "draft",
                    "note": "MOCK — real ERP integration in Phase 1 / Step 2.",
                },
            )

        if action == "create_note":
            return ConnectorResult(
                success=True,
                data={
                    "note_id": f"NOTE-MOCK-{secrets.token_hex(4).upper()}",
                    "status": "saved",
                    "note": "MOCK — real ERP integration in Phase 1 / Step 2.",
                },
            )

        if action == "lookup_counterparty":
            return ConnectorResult(
                success=True,
                data={
                    "results": [
                        {
                            "id": "CP-MOCK-001",
                            "name": payload.get("query"),
                            "country": "LT",
                            "vat": "LT100000000000",
                            "note": "MOCK result.",
                        }
                    ]
                },
            )

        return ConnectorResult(
            success=False,
            data={},
            error=f"Unknown action: {action}",
        )
