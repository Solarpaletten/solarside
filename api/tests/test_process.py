"""Test the /v1/process MVP endpoint with a mocked AI provider."""
from unittest.mock import AsyncMock, patch

import pytest

from solar_core.ai.providers import AICompletion


@pytest.fixture
def mock_anthropic_completion():
    """Patch AnthropicProvider.complete to return a deterministic response."""
    fake_completion = AICompletion(
        text="Это тестовое резюме на русском языке в двух предложениях. Все факты сохранены.",
        provider="anthropic",
        model="claude-sonnet-4-6",
        usage={"input_tokens": 50, "output_tokens": 30},
    )
    with patch(
        "solar_core.ai.providers.anthropic.AnthropicProvider.complete",
        new=AsyncMock(return_value=fake_completion),
    ), patch(
        "solar_core.ai.providers.anthropic.AnthropicProvider.is_available",
        return_value=True,
    ):
        yield fake_completion


@pytest.mark.asyncio
async def test_process_summarize_creates_document_and_action(
    client, auth_headers, mock_anthropic_completion
):
    response = await client.post(
        "/v1/process",
        headers=auth_headers,
        json={
            "text": "The European Commission today announced new sanctions against multiple entities related to ongoing geopolitical conflict.",
            "url": "https://example.com/news/123",
            "action": "summarize",
            "language": "ru",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["document_id"].startswith("doc_")
    assert body["action_id"].startswith("act_")
    assert body["action"] == "summarize"
    assert body["saved"] is True
    assert "summary" in body["result"]
    assert body["result"]["language"] == "ru"
    assert body["provider"] == "anthropic"


@pytest.mark.asyncio
async def test_process_then_get_document(
    client, auth_headers, mock_anthropic_completion
):
    create = await client.post(
        "/v1/process",
        headers=auth_headers,
        json={
            "text": "Some text to summarize.",
            "url": "https://example.com",
            "action": "summarize",
            "language": "en",
        },
    )
    assert create.status_code == 200
    doc_id = create.json()["document_id"]

    fetched = await client.get(f"/v1/documents/{doc_id}", headers=auth_headers)
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["id"] == doc_id
    assert body["source_url"] == "https://example.com"
    assert len(body["actions"]) == 1
    assert body["actions"][0]["type"] == "summarize"


@pytest.mark.asyncio
async def test_list_documents(client, auth_headers, mock_anthropic_completion):
    # Create two documents
    for i in range(2):
        await client.post(
            "/v1/process",
            headers=auth_headers,
            json={"text": f"Text {i}", "action": "summarize", "language": "en"},
        )

    response = await client.get("/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 2


@pytest.mark.asyncio
async def test_process_unknown_action_returns_500(client, auth_headers):
    response = await client.post(
        "/v1/process",
        headers=auth_headers,
        json={"text": "hi", "action": "magic"},  # invalid action
    )
    # Pydantic validation rejects it before reaching the handler
    assert response.status_code == 422
