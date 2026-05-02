"""Documents service: create, retrieve, list documents."""
import secrets
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from solar_core.core.exceptions import NotFoundError
from solar_core.db.models import SolarAction, SolarDocument


def _generate_id(prefix: str) -> str:
    """Generate a short unique ID like 'doc_a1b2c3d4'."""
    return f"{prefix}_{secrets.token_hex(8)}"


class DocumentService:
    """Service layer for SolarDocument operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        title: str,
        selected_text: str | None = None,
        source_url: str | None = None,
        ai_result: dict[str, Any] | None = None,
        language: str | None = None,
        vertical: str | None = None,
        user_id: str = "default",
    ) -> SolarDocument:
        """Create a new document."""
        doc = SolarDocument(
            id=_generate_id("doc"),
            title=title[:500],
            selected_text=selected_text,
            source_url=source_url,
            ai_result=ai_result,
            language=language,
            vertical=vertical,
            user_id=user_id,
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def add_action_record(
        self,
        *,
        document_id: str,
        action_type: str,
        status: str = "done",
        payload: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        duration_ms: int | None = None,
    ) -> SolarAction:
        """Record an action execution against a document."""
        action = SolarAction(
            id=_generate_id("act"),
            document_id=document_id,
            type=action_type,
            status=status,
            payload=payload,
            result=result,
            error=error,
            provider=provider,
            model=model,
            duration_ms=duration_ms,
        )
        self.db.add(action)
        await self.db.flush()
        return action

    async def get(self, document_id: str) -> SolarDocument:
        """Get a document by ID, including its actions."""
        stmt = (
            select(SolarDocument)
            .where(SolarDocument.id == document_id)
            .options(selectinload(SolarDocument.actions))
        )
        result = await self.db.execute(stmt)
        doc = result.scalar_one_or_none()
        if doc is None:
            raise NotFoundError(f"Document not found: {document_id}")
        return doc

    async def list(
        self,
        *,
        user_id: str = "default",
        limit: int = 50,
        offset: int = 0,
    ) -> list[SolarDocument]:
        """List documents for a user, newest first.

        Eagerly loads `actions` so callers can serialize without
        triggering lazy-IO outside the session scope.
        """
        stmt = (
            select(SolarDocument)
            .where(SolarDocument.user_id == user_id)
            .order_by(desc(SolarDocument.created_at))
            .limit(limit)
            .offset(offset)
            .options(selectinload(SolarDocument.actions))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
