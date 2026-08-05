"""API-facing Pydantic schemas, kept separate from the SQLModel table models
so the wire format can evolve independently of storage."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    """Base for schemas returned straight from SQLModel objects instead of
    hand-built dicts — needs from_attributes for Pydantic v2 to read them."""

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(ORMBase):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    num_pages: int
    num_chunks: int
    status: str
    error: str | None = None
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    message_count: int = 0


class MessageOut(ORMBase):
    id: str
    role: str
    content: str
    trace_id: str | None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: str | None = None


class RetrievedChunkOut(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: int
    text: str
    vector_score: float
    bm25_score: float
    fused_score: float
    rank: int


class TraceOut(ORMBase):
    id: str
    conversation_id: str
    raw_query: str
    condensed_query: str | None
    retrieved: list[dict]
    answer: str
    confidence: float
    low_confidence: bool
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: dict
    created_at: datetime


class TraceSummaryOut(BaseModel):
    id: str
    conversation_id: str
    raw_query: str
    confidence: float
    low_confidence: bool
    model: str
    total_latency_ms: float
    created_at: datetime
