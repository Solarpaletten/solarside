"""GET /v1/documents and GET /v1/documents/{id}."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from solar_core.api.schemas import DocumentListResponse, DocumentResponse
from solar_core.core.auth import verify_api_key
from solar_core.db import get_db
from solar_core.documents import DocumentService

router = APIRouter(prefix="/v1/documents", tags=["documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    dependencies=[Depends(verify_api_key)],
)
async def list_documents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    """List the most recent documents."""
    service = DocumentService(db)
    docs = await service.list(limit=limit, offset=offset)
    items = [DocumentResponse.model_validate(d) for d in docs]
    return DocumentListResponse(items=items, count=len(items))


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    dependencies=[Depends(verify_api_key)],
)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Retrieve a single document with all its action records."""
    service = DocumentService(db)
    doc = await service.get(document_id)
    return DocumentResponse.model_validate(doc)
