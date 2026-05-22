"""POST /v1/process — main MVP endpoint.

Workflow:
  1. Receive { text, url, action, language }
  2. Run the requested action via Actions Engine (calls AI Orchestrator)
  3. Persist a SolarDocument with the AI result
  4. Persist a SolarAction record linked to the document
  5. Return { document_id, action_id, result, ... }
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from solar_core.actions import ActionContext, get_registry
from solar_core.api.schemas import ProcessRequest, ProcessResponse
from solar_core.core.auth import verify_api_key
from solar_core.core.logging import get_logger
from solar_core.db import get_db
from solar_core.documents import DocumentService

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["process"])


@router.post(
    "/process",
    response_model=ProcessResponse,
    dependencies=[Depends(verify_api_key)],
)
async def process(
    req: ProcessRequest,
    db: AsyncSession = Depends(get_db),
) -> ProcessResponse:
    """The headline workflow: highlight → AI → action → save."""
    logger.info(
        "process_request",
        action=req.action,
        url=req.url,
        text_length=len(req.text),
        language=req.language,
    )

    # 1. Run the action
    registry = get_registry()
    action = registry.get(req.action)
    ctx = ActionContext(text=req.text, url=req.url, language=req.language)
    result = await action.execute(ctx)

    # 2. Build a sensible title
    title = req.title
    if not title:
        # Use first 80 chars of the text as a fallback title
        title = req.text.strip().split("\n", 1)[0][:80]
        if not title:
            title = f"Document via {req.action}"

    # 3. Persist document + action.
    # Air-first production may run WITHOUT a database. The AI action above has
    # already succeeded, so we never want a missing/unavailable DB to turn a
    # good result into a 500. If persistence fails, return the result with
    # saved=False instead of crashing — the user still gets their answer.
    try:
        docs = DocumentService(db)
        doc = await docs.create(
            title=title,
            selected_text=req.text,
            source_url=req.url,
            ai_result=result.data,
            language=req.language,
            vertical=req.vertical,
        )
        action_record = await docs.add_action_record(
            document_id=doc.id,
            action_type=req.action,
            status="done" if result.success else "failed",
            payload={"language": req.language, "url": req.url},
            result=result.data,
            error=result.error,
            provider=result.provider,
            model=result.model,
            duration_ms=result.duration_ms,
        )
        return ProcessResponse(
            document_id=doc.id,
            action_id=action_record.id,
            action=req.action,
            result=result.data,
            saved=True,
            provider=result.provider,
            model=result.model,
            duration_ms=result.duration_ms,
        )
    except Exception as exc:  # noqa: BLE001 — degrade gracefully without a DB
        logger.warning(
            "process_persist_skipped",
            action=req.action,
            detail=str(exc),
            note="Result returned to client unsaved (Air-first / DB unavailable).",
        )
        return ProcessResponse(
            document_id=None,
            action_id=None,
            action=req.action,
            result=result.data,
            saved=False,
            provider=result.provider,
            model=result.model,
            duration_ms=result.duration_ms,
        )
