"""Telegram connector — send messages to Telegram chats via Bot API.

Phase 1 / Step 3 — first delivery connector.

Supported actions:
  - send_message       (send arbitrary text to a chat)
  - send_result        (send the latest action result — selected text + AI output)

Configuration via .env:
  TELEGRAM_BOT_TOKEN          (required) — token from @BotFather
  TELEGRAM_DEFAULT_CHAT_ID    (optional) — default destination chat id
"""
from typing import Any

import httpx

from solar_core.config import get_telegram_settings
from solar_core.connectors.base import BaseConnector, ConnectorAction, ConnectorResult
from solar_core.core.logging import get_logger

logger = get_logger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"
DEFAULT_TIMEOUT_SECONDS = 10.0
# Telegram caps a single message at 4096 chars. We leave room for our framing.
MAX_MESSAGE_LENGTH = 4000


class TelegramConnector(BaseConnector):
    """Connector to Telegram Bot API."""

    name = "telegram"
    description = "Telegram — send messages to a chat or channel via your bot."

    def __init__(self):
        self.settings = get_telegram_settings()

    def is_available(self) -> bool:
        return bool(self.settings.bot_token)

    def list_actions(self) -> list[ConnectorAction]:
        return [
            ConnectorAction(
                name="send_message",
                description="Send an arbitrary text message to a Telegram chat.",
                params_schema={
                    "text": "string (required)",
                    "chat_id": "string | int (optional, falls back to TELEGRAM_DEFAULT_CHAT_ID)",
                },
            ),
            ConnectorAction(
                name="send_result",
                description="Send the latest action result to a Telegram chat.",
                params_schema={
                    "result_text": "string (required) — the AI result to send",
                    "chat_id": "string | int (optional)",
                },
            ),
        ]

    async def execute(self, action: str, payload: dict[str, Any]) -> ConnectorResult:
        """Dispatch to the correct handler."""
        if not self.is_available():
            return ConnectorResult(
                success=False,
                data={},
                error="Telegram connector not configured: TELEGRAM_BOT_TOKEN missing.",
            )

        if action in ("send_message", "send_result"):
            # send_result is a thin alias today; both just send text. We keep
            # them separate so the frontend can evolve formatting per action
            # without breaking the API contract.
            text_field = "result_text" if action == "send_result" else "text"
            text = (payload.get(text_field) or "").strip()
            if not text:
                return ConnectorResult(
                    success=False,
                    data={},
                    error=f"Missing required field: {text_field}",
                )

            chat_id = payload.get("chat_id") or self.settings.default_chat_id
            if not chat_id:
                return ConnectorResult(
                    success=False,
                    data={},
                    error=(
                        "No chat_id provided and TELEGRAM_DEFAULT_CHAT_ID is not set."
                    ),
                )

            return await self._send_message(chat_id=chat_id, text=text)

        return ConnectorResult(
            success=False,
            data={},
            error=f"Unknown action: {action}",
        )

    async def _send_message(self, chat_id: str | int, text: str) -> ConnectorResult:
        """Call Telegram's sendMessage endpoint."""
        # Truncate long messages politely rather than letting Telegram reject them.
        truncated = False
        if len(text) > MAX_MESSAGE_LENGTH:
            text = text[: MAX_MESSAGE_LENGTH - 20] + "\n\n…[truncated]"
            truncated = True

        url = f"{TELEGRAM_API_BASE}/bot{self.settings.bot_token}/sendMessage"
        body = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_SECONDS) as client:
                resp = await client.post(url, json=body)
                data = resp.json()
        except httpx.HTTPError as e:
            logger.warning("telegram_send_failed", error=str(e))
            return ConnectorResult(
                success=False,
                data={},
                error=f"Network error talking to Telegram: {e}",
            )

        if not data.get("ok"):
            description = data.get("description", "unknown error")
            logger.warning(
                "telegram_send_rejected",
                description=description,
                error_code=data.get("error_code"),
            )
            return ConnectorResult(
                success=False,
                data={},
                error=f"Telegram API error: {description}",
            )

        result = data.get("result", {})
        logger.info(
            "telegram_send_ok",
            message_id=result.get("message_id"),
            chat_id=chat_id,
            length=len(text),
            truncated=truncated,
        )
        return ConnectorResult(
            success=True,
            data={
                "message_id": result.get("message_id"),
                "chat_id": chat_id,
                "truncated": truncated,
            },
        )
