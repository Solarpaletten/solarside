"""Test the health endpoint."""
import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    response = await client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "ai_providers" in body


@pytest.mark.asyncio
async def test_root_returns_metadata(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["name"] == "Solar Core"
