"""Pydantic request/response schemas for the API."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------- /v1/process ----------


class ProcessRequest(BaseModel):
    """The MVP flow request: 'I highlighted some text, do something with it'."""

    text: str = Field(..., min_length=1, max_length=100_000, description="Selected text.")
    url: str | None = Field(None, description="Source URL.")
    action: Literal["summarize", "extract", "translate"] = Field(
        ..., description="Built-in action to run."
    )
    language: str = Field(default="en", description="Target language (ISO code).")
    title: str | None = Field(
        None,
        description="Optional title for the saved document. Auto-derived if omitted.",
    )
    vertical: str | None = Field(
        None,
        description="Vertical hint: legal | logistics | finance | ...",
    )


class ProcessResponse(BaseModel):
    # Optional: in Air-first / DB-unavailable mode the AI result is returned
    # unsaved, so these IDs are None and `saved` is False.
    document_id: str | None = None
    action_id: str | None = None
    action: str
    result: dict[str, Any]
    saved: bool = True
    provider: str | None = None
    model: str | None = None
    duration_ms: int | None = None


# ---------- /v1/documents ----------


class ActionRecord(BaseModel):
    id: str
    type: str
    status: str
    result: dict[str, Any] | None = None
    provider: str | None = None
    model: str | None = None
    duration_ms: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentResponse(BaseModel):
    id: str
    title: str
    source_url: str | None = None
    selected_text: str | None = None
    ai_result: dict[str, Any] | None = None
    language: str | None = None
    vertical: str | None = None
    created_at: datetime
    updated_at: datetime
    actions: list[ActionRecord] = []

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    count: int


# ---------- /v1/health ----------


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    ai_providers: dict[str, bool]


# ---------- /v1/connectors ----------


class ConnectorActionInfo(BaseModel):
    name: str
    description: str


class ConnectorInfo(BaseModel):
    name: str
    description: str
    available: bool
    actions: list[ConnectorActionInfo]


class ConnectorListResponse(BaseModel):
    items: list[ConnectorInfo]


# ---------- /v1/action ----------


class ActionRequest(BaseModel):
    """Direct connector action invocation."""

    connector: str = Field(..., description="Connector name, e.g. 'solar_erp'.")
    action: str = Field(..., description="Action name, e.g. 'create_invoice'.")
    payload: dict[str, Any] = Field(default_factory=dict)
    document_id: str | None = Field(
        None,
        description="If provided, the action will be linked to this document.",
    )


class ActionResponse(BaseModel):
    success: bool
    data: dict[str, Any]
    error: str | None = None
    action_id: str | None = None
