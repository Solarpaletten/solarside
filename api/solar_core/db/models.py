"""SQLAlchemy ORM models for Solar Core."""
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# pgvector — опционально (для PostgreSQL); на SQLite используется JSON-fallback
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False


def _utcnow() -> datetime:
    """Timezone-aware UTC now."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class SolarDocument(Base):
    """A saved snippet/highlight from the web with AI-processed result."""

    __tablename__ = "solar_documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    selected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ru/en/lt/de
    vertical: Mapped[str | None] = mapped_column(String(50), nullable=True)  # legal/logistics/finance
    user_id: Mapped[str] = mapped_column(String(64), default="default")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    # Embedding for semantic search (pgvector on PostgreSQL, JSON on SQLite for dev)
    if HAS_PGVECTOR:
        embedding: Mapped[list[float] | None] = mapped_column(
            Vector(1536), nullable=True
        )
    else:
        embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)

    actions: Mapped[list["SolarAction"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class SolarAction(Base):
    """An action executed on a document (summarize, extract, send_to_crm, ...)."""

    __tablename__ = "solar_actions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("solar_documents.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(50))  # summarize | extract | translate | ...
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending | running | done | failed
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    document: Mapped["SolarDocument"] = relationship(back_populates="actions")
