"""Orchestrates one chat turn end to end, yielding SSE events as it goes so
the frontend can show progressive status instead of one blocking spinner.

Flow: validate -> condense question (if there's history) -> hybrid retrieve
-> confidence check -> build grounded prompt -> stream Claude -> persist
Message + Trace rows.
"""
import time
from collections.abc import AsyncIterator
from typing import Any

from sqlmodel import Session, select

from app.config import get_settings
from app.logging_config import get_logger, log_event
from app.models import Conversation, Message, MessageRole, Trace
from app.rag import llm
from app.rag.guardrails import GuardrailError, assess_confidence, validate_message
from app.rag.prompts import (
    LOW_CONFIDENCE_PREFIX,
    NO_CONTEXT_MESSAGE,
    SYSTEM_PROMPT,
    format_context,
    format_history,
)
from app.rag.retriever import RetrievedChunk, hybrid_retrieve, top_confidence
from app.rag.vectorstore import get_collection

logger = get_logger("rag.pipeline")


def _get_or_create_conversation(session: Session, conversation_id: str | None, first_message: str) -> Conversation:
    if conversation_id:
        conv = session.get(Conversation, conversation_id)
        if conv:
            return conv
    title = first_message.strip().splitlines()[0][:60]
    conv = Conversation(title=title or "New conversation")
    session.add(conv)
    session.commit()
    session.refresh(conv)
    return conv


def _recent_history(session: Session, conversation_id: str, max_turns: int) -> list[tuple[str, str]]:
    messages = session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    ).all()
    trimmed = messages[-(max_turns * 2):]
    return [(m.role.value, m.content) for m in trimmed]


def _chunk_to_dict(chunk: RetrievedChunk) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "filename": chunk.filename,
        "page": chunk.page,
        "text": chunk.text,
        "vector_score": chunk.vector_score,
        "bm25_score": chunk.bm25_score,
        "fused_score": chunk.fused_score,
        "rank": chunk.rank,
    }


async def run_chat_turn(session: Session, conversation_id: str | None, raw_message: str) -> AsyncIterator[dict]:
    settings = get_settings()
    t_start = time.perf_counter()

    try:
        user_text = validate_message(raw_message)
    except GuardrailError as exc:
        yield {"type": "error", "message": exc.message}
        return

    conversation = _get_or_create_conversation(session, conversation_id, user_text)
    history = _recent_history(session, conversation.id, settings.max_history_turns)

    session.add(Message(conversation_id=conversation.id, role=MessageRole.user, content=user_text))
    session.commit()

    yield {"type": "meta", "conversation_id": conversation.id}

    try:
        async for event in _run_retrieval_and_generation(session, conversation, history, user_text, settings, t_start):
            yield event
    except Exception:
        # Anthropic errors, network blips, whatever — surface one clean SSE
        # error event instead of dropping the connection mid-stream.
        logger.exception("chat turn failed", extra={"extra_fields": {"conversation_id": conversation.id}})
        yield {"type": "error", "message": "Something went wrong while generating the answer. Please try again."}


async def _run_retrieval_and_generation(
    session: Session,
    conversation: Conversation,
    history: list[tuple[str, str]],
    user_text: str,
    settings,
    t_start: float,
) -> AsyncIterator[dict]:
    # --- condense question (only if there is prior context worth resolving) ---
    t0 = time.perf_counter()
    condensed_query = user_text
    if len(history) >= settings.condense_after_turns * 2:
        condensed_query = await llm.condense_question(format_history(history), user_text)
    condense_ms = (time.perf_counter() - t0) * 1000

    # --- retrieval ---
    yield {"type": "status", "stage": "retrieving"}
    t0 = time.perf_counter()
    if get_collection().count() == 0:
        retrieved: list[RetrievedChunk] = []
    else:
        retrieved = hybrid_retrieve(session, condensed_query)
    retrieval_ms = (time.perf_counter() - t0) * 1000

    retrieved_dicts = [_chunk_to_dict(c) for c in retrieved]
    confidence, low_confidence = assess_confidence(top_confidence(retrieved))

    yield {"type": "sources", "sources": retrieved_dicts, "low_confidence": low_confidence, "confidence": confidence}

    # --- no documents at all: short-circuit, skip the LLM entirely ---
    if not retrieved:
        answer = NO_CONTEXT_MESSAGE
        yield {"type": "delta", "text": answer}
        session.add(Message(conversation_id=conversation.id, role=MessageRole.assistant, content=answer))
        session.commit()
        trace = Trace(
            conversation_id=conversation.id,
            raw_query=user_text,
            condensed_query=condensed_query if condensed_query != user_text else None,
            retrieved=[],
            answer=answer,
            confidence=0.0,
            low_confidence=True,
            model="none",
            latency_ms={
                "condense_ms": round(condense_ms, 1),
                "retrieval_ms": round(retrieval_ms, 1),
                "generation_ms": 0.0,
                "total_ms": round((time.perf_counter() - t_start) * 1000, 1),
            },
        )
        session.add(trace)
        session.commit()
        yield {"type": "done", "trace_id": trace.id, "conversation_id": conversation.id}
        return

    # --- generation ---
    system_prompt = SYSTEM_PROMPT.format(context=format_context(retrieved_dicts))
    yield {"type": "status", "stage": "generating"}

    answer_parts: list[str] = []
    if low_confidence:
        answer_parts.append(LOW_CONFIDENCE_PREFIX)
        yield {"type": "delta", "text": LOW_CONFIDENCE_PREFIX}

    t0 = time.perf_counter()
    usage = {"input_tokens": 0, "output_tokens": 0}
    async for event in llm.stream_answer(system_prompt, history, user_text):
        if event["type"] == "delta":
            answer_parts.append(event["text"])
            yield {"type": "delta", "text": event["text"]}
        elif event["type"] == "usage":
            usage = event
    generation_ms = (time.perf_counter() - t0) * 1000

    answer = "".join(answer_parts)
    session.add(Message(conversation_id=conversation.id, role=MessageRole.assistant, content=answer))
    session.commit()

    trace = Trace(
        conversation_id=conversation.id,
        raw_query=user_text,
        condensed_query=condensed_query if condensed_query != user_text else None,
        retrieved=retrieved_dicts,
        answer=answer,
        confidence=confidence,
        low_confidence=low_confidence,
        model=settings.anthropic_model,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        latency_ms={
            "condense_ms": round(condense_ms, 1),
            "retrieval_ms": round(retrieval_ms, 1),
            "generation_ms": round(generation_ms, 1),
            "total_ms": round((time.perf_counter() - t_start) * 1000, 1),
        },
    )
    session.add(trace)
    session.commit()
    session.refresh(trace)

    log_event(logger, "chat turn complete", conversation_id=conversation.id, trace_id=trace.id,
              confidence=confidence, low_confidence=low_confidence,
              retrieved_count=len(retrieved), **trace.latency_ms)

    yield {"type": "done", "trace_id": trace.id, "conversation_id": conversation.id}
