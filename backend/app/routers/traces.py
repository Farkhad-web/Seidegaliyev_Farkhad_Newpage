"""Read-only endpoints backing the frontend's Observability panel: a list of
recent RAG traces and the full detail (retrieved chunks, scores, latency
breakdown, token usage) for one trace."""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette.status import HTTP_404_NOT_FOUND

from app.db import get_session
from app.models import Trace
from app.schemas import TraceOut, TraceSummaryOut

router = APIRouter(prefix="/api/traces", tags=["traces"])


@router.get("", response_model=list[TraceSummaryOut])
def list_traces(limit: int = 50, session: Session = Depends(get_session)) -> list[TraceSummaryOut]:
    traces = session.exec(select(Trace).order_by(Trace.created_at.desc()).limit(limit)).all()
    return [
        TraceSummaryOut(
            id=t.id,
            conversation_id=t.conversation_id,
            raw_query=t.raw_query,
            confidence=t.confidence,
            low_confidence=t.low_confidence,
            model=t.model,
            total_latency_ms=t.latency_ms.get("total_ms", 0.0),
            created_at=t.created_at,
        )
        for t in traces
    ]


@router.get("/{trace_id}", response_model=TraceOut)
def get_trace(trace_id: str, session: Session = Depends(get_session)) -> Trace:
    trace = session.get(Trace, trace_id)
    if not trace:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Trace not found")
    return trace
