from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlmodel import Session, func, select
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from app.db import get_session
from app.logging_config import get_logger, log_event
from app.models import Document
from app.rag.guardrails import validate_upload
from app.rag.ingestion import delete_document, ingest_document
from app.rate_limit import SlidingWindowLimiter, client_key
from app.schemas import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = get_logger("api.documents")


def _limiter(request: Request) -> SlidingWindowLimiter:
    return request.app.state.upload_limiter


@router.get("", response_model=list[DocumentOut])
def list_documents(session: Session = Depends(get_session)) -> list[Document]:
    return session.exec(select(Document).order_by(Document.created_at.desc())).all()


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile,
    session: Session = Depends(get_session),
) -> Document:
    _limiter(request).check(client_key(request))

    content = await file.read()
    existing_count = session.exec(select(func.count()).select_from(Document)).one()
    validation = validate_upload(file.filename or "", len(content), existing_count)
    if not validation.ok:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=validation.reason)

    document = ingest_document(session, file.filename or "upload", file.content_type or "", content)
    log_event(logger, "document upload", filename=document.filename, status=document.status)
    if document.status == "failed":
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=document.error)
    return document


@router.delete("/{document_id}", status_code=204)
def remove_document(document_id: str, session: Session = Depends(get_session)) -> None:
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Document not found")
    delete_document(session, document)
    log_event(logger, "document deleted", document_id=document_id)
