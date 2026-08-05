"""SQLModel tables.

Vectors live in Chroma; SQLite is the system of record for everything else,
including the *text* of each chunk (needed to rebuild the BM25 index and to
render source snippets in the UI without a round trip to Chroma).
"""
import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlmodel import JSON, Column, Field, SQLModel


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return uuid.uuid4().hex


class DocumentStatus(str, Enum):
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Document(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    filename: str
    content_type: str
    size_bytes: int
    num_pages: int = 0
    num_chunks: int = 0
    status: DocumentStatus = DocumentStatus.processing
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)


class Chunk(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    document_id: str = Field(foreign_key="document.id", index=True)
    filename: str
    page: int
    chunk_index: int
    text: str
    char_count: int


class Conversation(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    title: str = "New conversation"
    created_at: datetime = Field(default_factory=_now)


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class Message(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    role: MessageRole
    content: str
    trace_id: str | None = Field(default=None, foreign_key="trace.id")
    created_at: datetime = Field(default_factory=_now)


class Trace(SQLModel, table=True):
    """One row per assistant turn: everything needed to audit *why* the
    model answered the way it did, surfaced in the Observability panel."""

    id: str = Field(default_factory=_uuid, primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id", index=True)
    raw_query: str
    condensed_query: str | None = None
    retrieved: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    answer: str = ""
    confidence: float = 0.0
    low_confidence: bool = False
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: dict = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=_now)
