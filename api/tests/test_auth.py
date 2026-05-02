"""Test API key authentication."""
import pytest


@pytest.mark.asyncio
async def test_process_without_api_key_returns_401(client):
    response = await client.post(
        "/v1/process",
        json={"text": "hello", "action": "summarize"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_process_with_wrong_api_key_returns_401(client):
    response = await client.post(
        "/v1/process",
        json={"text": "hello", "action": "summarize"},
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_documents_without_api_key_returns_401(client):
    response = await client.get("/v1/documents")
    assert response.status_code == 401
