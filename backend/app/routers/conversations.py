from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, func, select
from starlette.status import HTTP_404_NOT_FOUND

from app.db import get_session
from app.models import Conversation, Message
from app.schemas import ConversationOut, MessageOut

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationOut])
def list_conversations(session: Session = Depends(get_session)) -> list[ConversationOut]:
    conversations = session.exec(select(Conversation).order_by(Conversation.created_at.desc())).all()
    out = []
    for conv in conversations:
        count = session.exec(
            select(func.count()).select_from(Message).where(Message.conversation_id == conv.id)
        ).one()
        out.append(ConversationOut(**conv.model_dump(), message_count=count))
    return out


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(conversation_id: str, session: Session = Depends(get_session)) -> list[Message]:
    conv = session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Conversation not found")
    return session.exec(
        select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
    ).all()


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, session: Session = Depends(get_session)) -> None:
    conv = session.get(Conversation, conversation_id)
    if not conv:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Conversation not found")
    for message in session.exec(select(Message).where(Message.conversation_id == conversation_id)).all():
        session.delete(message)
    session.delete(conv)
    session.commit()
