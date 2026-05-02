"""Test connectors registry and Solar ERP connector mock."""
import pytest


@pytest.mark.asyncio
async def test_list_connectors(client, auth_headers):
    response = await client.get("/v1/connectors", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    names = [c["name"] for c in body["items"]]
    assert "solar_erp" in names

    # solar_erp should expose the flagship actions
    erp = next(c for c in body["items"] if c["name"] == "solar_erp")
    action_names = [a["name"] for a in erp["actions"]]
    assert "create_invoice" in action_names
    assert "create_cmr" in action_names
    assert "create_note" in action_names
    assert "lookup_counterparty" in action_names


@pytest.mark.asyncio
async def test_invoke_solar_erp_create_invoice_mock(client, auth_headers):
    response = await client.post(
        "/v1/action",
        headers=auth_headers,
        json={
            "connector": "solar_erp",
            "action": "create_invoice",
            "payload": {
                "entity": "Melasa Rail",
                "counterparty": "Test GmbH",
                "amount": 1000,
                "currency": "EUR",
                "items": [],
            },
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    assert body["data"]["invoice_id"].startswith("INV-MOCK-")


@pytest.mark.asyncio
async def test_invoke_unknown_connector_returns_502(client, auth_headers):
    response = await client.post(
        "/v1/action",
        headers=auth_headers,
        json={"connector": "nonexistent", "action": "anything", "payload": {}},
    )
    assert response.status_code == 502
