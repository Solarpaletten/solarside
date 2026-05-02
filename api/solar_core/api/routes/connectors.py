"""POST /v1/action and GET /v1/connectors."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from solar_core.api.schemas import (
    ActionRequest,
    ActionResponse,
    ConnectorActionInfo,
    ConnectorInfo,
    ConnectorListResponse,
)
from solar_core.connectors import get_connector_registry
from solar_core.core.auth import verify_api_key
from solar_core.core.logging import get_logger
from solar_core.db import get_db
from solar_core.documents import DocumentService

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["connectors"])


@router.get(
    "/connectors",
    response_model=ConnectorListResponse,
    dependencies=[Depends(verify_api_key)],
)
async def list_connectors() -> ConnectorListResponse:
    """List available connectors and their actions."""
    registry = get_connector_registry()
    items = []
    for c in registry.list_connectors():
        items.append(
            ConnectorInfo(
                name=c["name"],
                description=c["description"],
                available=c["available"],
                actions=[
                    ConnectorActionInfo(name=a["name"], description=a["description"])
                    for a in c["actions"]
                ],
            )
        )
    return ConnectorListResponse(items=items)


@router.post(
    "/action",
    response_model=ActionResponse,
    dependencies=[Depends(verify_api_key)],
)
async def execute_action(
    req: ActionRequest,
    db: AsyncSession = Depends(get_db),
) -> ActionResponse:
    """Execute a connector action. Optionally link it to a document."""
    logger.info(
        "connector_action",
        connector=req.connector,
        action=req.action,
        document_id=req.document_id,
    )
    registry = get_connector_registry()
    connector = registry.get(req.connector)
    result = await connector.execute(req.action, req.payload)

    action_id: str | None = None
    if req.document_id:
        docs = DocumentService(db)
        action_record = await docs.add_action_record(
            document_id=req.document_id,
            action_type=f"{req.connector}.{req.action}",
            status="done" if result.success else "failed",
            payload=req.payload,
            result=result.data,
            error=result.error,
            provider=req.connector,
        )
        action_id = action_record.id

    return ActionResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        action_id=action_id,
    )
