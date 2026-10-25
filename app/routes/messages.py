from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.extensions import get_db
from app.models.user import User
from app.models.messages import Messages
from app.models.ai_memory import AIPersonalMemory
from app.models.insight import Insight
from app.schemas.message import MessageCreate, MessageResponse, MessageEdit, ForwardRequest
from app.schemas.ai_memory import AIPersonalMemoryCreate, AIPersonalMemoryResponse
from app.utils.auth import get_current_user
from app.utils.i18n import t, user_language

from app.services.ai_chat_service import ai_chat
from app.middleware.activity import log_activity

router = APIRouter(prefix="/messages", tags=["messages"])


def get_or_create_ai_user(db: Session):
    ai_user = db.query(User).filter_by(username="ai_assistant").first()
    if ai_user:
        return ai_user

    ai_user = User(
        username="ai_assistant",
        email="ai_assistant@local.ohmatt",
        timezone="UTC",
        preferences={
            "currency": "USD",
            "date_format": "YYYY-MM-DD",
            "notifications": False,
        },
    )
    ai_user.set_password("not-a-login-account")
    db.add(ai_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.query(User).filter_by(username="ai_assistant").one()
    db.refresh(ai_user)
    return ai_user


def serialize_ai_message(message, current_user, ai_user, legacy_role=None):
    if legacy_role:
        role = legacy_role
    elif message.sender_id == ai_user.id:
        role = "assistant"
    else:
        role = "user"

    return {
        "id": message.id,
        "role": role,
        "content": message.content,
        "timestamp": message.timestamp.isoformat() if message.timestamp else None,
        "is_read": message.is_read,
    }


@router.get("", response_model=List[MessageResponse])
async def get_messages(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a bounded page of messages for the current user."""
    messages = (
        db.query(Messages)
        .options(joinedload(Messages.sender), joinedload(Messages.receiver))
        .filter(
            (Messages.sender_id == current_user.id) |
            (Messages.receiver_id == current_user.id)
        )
        .order_by(Messages.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": m.id,
            "sender": m.sender.username if m.sender else "Unknown",
            "receiver": m.receiver.username if m.receiver else "Unknown",
            "content": m.content,
            "timestamp": m.timestamp.isoformat() if m.timestamp else None,
            "is_read": m.is_read,
            "status": m.status,
            "is_edited": m.is_edited,
            "is_deleted": m.is_deleted,
        }
        for m in messages
    ]





@router.get("/ai")
async def get_ai_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personal AI chat history with explicit message roles"""
    ai_user = get_or_create_ai_user(db)

    ai_messages = list(reversed(
        db.query(Messages)
        .filter(
            ((Messages.sender_id == current_user.id) & (Messages.receiver_id == ai_user.id)) |
            ((Messages.sender_id == ai_user.id) & (Messages.receiver_id == current_user.id)),
            Messages.is_deleted.is_not(True),
        )
        .order_by(Messages.timestamp.desc(), Messages.id.desc())
        .limit(500)
        .all()
    ))

    legacy_messages = list(reversed(
        db.query(Messages)
        .filter(
            Messages.sender_id == current_user.id,
            Messages.receiver_id == current_user.id,
            Messages.is_deleted.is_not(True),
        )
        .order_by(Messages.timestamp.desc(), Messages.id.desc())
        .limit(500)
        .all()
    ))

    serialized = [
        serialize_ai_message(message, current_user, ai_user)
        for message in ai_messages
    ]

    # Older AI chats were stored as self-to-self pairs before the assistant
    # account existed. Preserve that history with deterministic pair roles.
    for index, message in enumerate(legacy_messages):
        serialized.append(
            serialize_ai_message(
                message,
                current_user,
                ai_user,
                legacy_role="user" if index % 2 == 0 else "assistant"
            )
        )

    serialized.sort(key=lambda item: (item["timestamp"] or "", item["id"]))
    return serialized


def _delete_ai_history(db: Session, user_id: int, ai_user_id: int) -> int:
    ai_message_ids = select(Messages.id).where(
            ((Messages.sender_id == user_id) & (Messages.receiver_id == ai_user_id)) |
            ((Messages.sender_id == ai_user_id) & (Messages.receiver_id == user_id)) |
            ((Messages.sender_id == user_id) & (Messages.receiver_id == user_id))
    )
    db.query(Messages).filter(Messages.forwarded_from_id.in_(ai_message_ids)).update(
        {Messages.forwarded_from_id: None},
        synchronize_session=False,
    )
    deleted_ai_messages = (
        db.query(Messages)
        .filter(
            ((Messages.sender_id == user_id) & (Messages.receiver_id == ai_user_id)) |
            ((Messages.sender_id == ai_user_id) & (Messages.receiver_id == user_id))
        )
        .delete(synchronize_session=False)
    )
    deleted_legacy_messages = (
        db.query(Messages)
        .filter(Messages.sender_id == user_id, Messages.receiver_id == user_id)
        .delete(synchronize_session=False)
    )
    return deleted_ai_messages + deleted_legacy_messages


@router.get("/ai/memories", response_model=List[AIPersonalMemoryResponse])
def get_ai_memories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(AIPersonalMemory)
        .filter(AIPersonalMemory.user_id == current_user.id)
        .order_by(AIPersonalMemory.created_at.desc(), AIPersonalMemory.id.desc())
        .limit(50)
        .all()
    )


@router.post("/ai/memories", response_model=AIPersonalMemoryResponse, status_code=201)
def create_ai_memory(
    data: AIPersonalMemoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = data.content.strip()
    if not content:
        raise HTTPException(422, "Memory cannot be empty")

    db.query(User.id).filter(User.id == current_user.id).with_for_update().one()
    count = (
        db.query(func.count(AIPersonalMemory.id))
        .filter(AIPersonalMemory.user_id == current_user.id)
        .scalar()
        or 0
    )
    if count >= 50:
        raise HTTPException(409, "Personal memory limit reached")

    memory = AIPersonalMemory(user_id=current_user.id, content=content)
    db.add(memory)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This personal memory already exists")
    db.refresh(memory)
    return memory


@router.delete("/ai/memories/{memory_id}")
def delete_ai_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    memory = (
        db.query(AIPersonalMemory)
        .filter(
            AIPersonalMemory.id == memory_id,
            AIPersonalMemory.user_id == current_user.id,
        )
        .first()
    )
    if not memory:
        raise HTTPException(404, "Memory not found")
    db.delete(memory)
    db.commit()
    return {"deleted": True}


@router.delete("/ai/history")
def clear_ai_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ai_user = get_or_create_ai_user(db)
    deleted_count = _delete_ai_history(db, current_user.id, ai_user.id)
    db.commit()
    return {"deleted_messages": deleted_count, "memories_preserved": True}


@router.delete("/ai/data")
def delete_ai_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ai_user = get_or_create_ai_user(db)
    deleted_count = _delete_ai_history(db, current_user.id, ai_user.id)
    deleted_memories = (
        db.query(AIPersonalMemory)
        .filter(AIPersonalMemory.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"deleted_messages": deleted_count, "deleted_memories": deleted_memories}


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread messages"""
    count = (
        db.query(Messages)
        .filter_by(receiver_id=current_user.id, is_read=False)
        .count()
    )
    return {"unread": count}


@router.get("/notification-summary")
async def notification_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return lightweight navigation badge counts without loading message bodies."""
    ai_user = db.query(User.id).filter(User.username == "ai_assistant").scalar()
    chat_count = 0
    if ai_user:
        chat_count = (
            db.query(func.count(Messages.id))
            .filter(
                Messages.receiver_id == current_user.id,
                Messages.sender_id == ai_user,
                Messages.is_read == False,
            )
            .scalar()
            or 0
        )

    message_query = db.query(func.count(Messages.id)).filter(
        Messages.receiver_id == current_user.id,
        Messages.is_read == False,
        Messages.sender_id != current_user.id,
    )
    if ai_user:
        message_query = message_query.filter(Messages.sender_id != ai_user)

    return {
        "chat": chat_count,
        "messages": message_query.scalar() or 0,
        "insights": (
            db.query(func.count(Insight.id))
            .filter(Insight.user_id == current_user.id, Insight.is_read == False)
            .scalar()
            or 0
        ),
    }

@router.post("", response_model=dict)
async def send_message(
        data: MessageCreate,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Send a message - AI responds if sending to ai_assistant"""

    if data.receiver_username == "ai_assistant":
        receiver = get_or_create_ai_user(db)
    else:
        receiver = db.query(User).filter_by(username=data.receiver_username).first()
        if not receiver:
            raise HTTPException(404, "Receiver not found")

    # Store user's message
    user_msg = Messages(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=data.content,
        is_read=data.receiver_username == "ai_assistant",
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    log_activity(db,
        request,
        current_user.id,
        "message_sent",
        entity_type="message",
        entity_id=user_msg.id,
        description=f"Sent message to {data.receiver_username}",
        metadata={"receiver": data.receiver_username},
    )

    # If messaging AI, get smart response
    if data.receiver_username == "ai_assistant":
        ai_response = ai_chat.respond(
            db,
            current_user,
            data.content,
            ai_user_id=receiver.id,
            exclude_message_id=user_msg.id,
        )

        ai_msg = Messages(
            sender_id=receiver.id,
            receiver_id=current_user.id,
            content=ai_response,
        )
        db.add(ai_msg)
        db.commit()
        db.refresh(ai_msg)
        log_activity(db,
            request,
            current_user.id,
            "ai_chat_interaction",
            entity_type="message",
            entity_id=ai_msg.id,
            description="Personal AI chat interaction",
            metadata={"prompt_message_id": user_msg.id, "response_message_id": ai_msg.id},
        )
        return {
            "id": ai_msg.id,
            "sender": "ai_assistant",
            "receiver": current_user.username,
            "content": ai_response,
            "timestamp": ai_msg.timestamp.isoformat(),
            "is_read": False,
        }

    # Regular user-to-user message
    log_activity(db,
        request,
        receiver.id,
        "message_received",
        entity_type="message",
        entity_id=user_msg.id,
        description=f"Received message from {current_user.username}",
        metadata={"sender": current_user.username},
    )
    return {
        "id": user_msg.id,
        "sender": current_user.username,
        "receiver": data.receiver_username,
        "content": data.content,
        "timestamp": user_msg.timestamp.isoformat(),
        "is_read": False,
    }


# app/routes/messages.py - add these endpoints

@router.put("/{message_id}/delivered")
def mark_delivered(
        message_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Mark message as delivered"""
    msg = db.get(Messages, message_id)
    if not msg or msg.receiver_id != current_user.id:
        raise HTTPException(404, "Message not found")
    if msg.status == "sent":
        msg.status = "delivered"
        msg.delivered_at = datetime.utcnow()
        db.commit()
    return {"status": msg.status}


@router.put("/{message_id}/read")
def mark_read(
        message_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Mark message as read"""
    msg = db.get(Messages, message_id)
    if not msg or msg.receiver_id != current_user.id:
        raise HTTPException(404, "Message not found")
    if msg.status in ("sent", "delivered"):
        msg.status = "read"
    msg.is_read = True
    msg.read_at = datetime.utcnow()
    db.commit()
    return {"status": msg.status, "read_at": msg.read_at.isoformat() if msg.read_at else None}


@router.put("/{message_id}/edit")
def edit_message(
        message_id: int,
        data: MessageEdit,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Edit a sent message"""
    msg = db.get(Messages, message_id)
    if not msg or msg.sender_id != current_user.id:
        raise HTTPException(404, "Message not found")
    if msg.is_deleted:
        raise HTTPException(400, "Cannot edit deleted message")

    msg.content = data.content
    msg.is_edited = True
    msg.edited_at = datetime.utcnow()
    db.commit()
    return {"message": t("message_edited", lang=user_language(current_user)), "edited_at": msg.edited_at.isoformat()}


@router.delete("/{message_id}")
def delete_message(
        message_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Soft delete a message"""
    msg = db.get(Messages, message_id)
    if not msg or msg.sender_id != current_user.id:
        raise HTTPException(404, "Message not found")

    msg.is_deleted = True
    msg.deleted_at = datetime.utcnow()
    db.commit()
    return {"message": t("message_deleted", lang=user_language(current_user))}


@router.post("/{message_id}/forward")
def forward_message(
        message_id: int,
        data: ForwardRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Forward a message to another user"""
    original = db.get(Messages, message_id)
    if not original:
        raise HTTPException(404, "Message not found")

    receiver = db.query(User).filter_by(username=data.receiver_username).first()
    if not receiver:
        raise HTTPException(404, "Receiver not found")

    forwarded = Messages(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=original.content,
        forwarded_from_id=original.id,
    )
    db.add(forwarded)
    db.commit()
    db.refresh(forwarded)
    return {"message": t("message_forwarded", lang=user_language(current_user)), "id": forwarded.id}
