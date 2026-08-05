import json

from fastapi import APIRouter, Depends, Request
from sse_starlette.sse import EventSourceResponse
from sqlmodel import Session

from app.db import get_session
from app.rag.pipeline import run_chat_turn
from app.rate_limit import SlidingWindowLimiter, client_key
from app.schemas import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat(
    request: Request,
    body: ChatRequest,
    session: Session = Depends(get_session),
) -> EventSourceResponse:
    limiter: SlidingWindowLimiter = request.app.state.chat_limiter
    limiter.check(client_key(request))

    async def event_stream():
        async for event in run_chat_turn(session, body.conversation_id, body.message):
            yield {"event": event["type"], "data": json.dumps(event)}

    return EventSourceResponse(event_stream())
