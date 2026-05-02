#!/usr/bin/env bash
# ----------------------------------------------------------------------
# Solar Core — quick smoke test of the MVP flow.
# Usage:  ./scripts/demo.sh
# ----------------------------------------------------------------------
set -euo pipefail

API="${SOLAR_API:-http://localhost:8000}"
KEY="${SOLAR_API_KEY:-dev-key-1}"

echo "=== 1. Health check ==="
curl -sS "$API/v1/health" | python -m json.tool

echo
echo "=== 2. List connectors ==="
curl -sS "$API/v1/connectors" -H "X-API-Key: $KEY" | python -m json.tool

echo
echo "=== 3. Process: summarize a snippet in Russian ==="
curl -sS -X POST "$API/v1/process" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $KEY" \
    -d '{
        "text": "The European Commission today announced new sanctions targeting entities involved in railway logistics across Eastern Europe, citing concerns about dual-use cargo classification and customs misdeclaration.",
        "url": "https://example.com/eu-sanctions-2026",
        "action": "summarize",
        "language": "ru",
        "vertical": "logistics"
    }' | python -m json.tool

echo
echo "=== 4. List recent documents ==="
curl -sS "$API/v1/documents?limit=5" -H "X-API-Key: $KEY" | python -m json.tool

echo
echo "=== 5. Mock-create an invoice in Solar ERP ==="
curl -sS -X POST "$API/v1/action" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $KEY" \
    -d '{
        "connector": "solar_erp",
        "action": "create_invoice",
        "payload": {
            "entity": "Vagonupaletas",
            "counterparty": "Test Logistics SIA",
            "amount": 12500.50,
            "currency": "EUR",
            "items": [{"name": "Wagon transport service", "qty": 1, "price": 12500.50}]
        }
    }' | python -m json.tool
