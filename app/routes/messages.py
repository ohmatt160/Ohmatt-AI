from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.extensions import get_db, db_session
from app.models.user import User
from app.models.messages import Messages
from app.schemas.message import MessageCreate, MessageResponse, MessageEdit, ForwardRequest
from app.utils.auth import get_current_user

from app.services.ai_chat_service import ai_chat
from app.middleware.activity import log_activity

router = APIRouter(prefix="/messages", tags=["messages"])


def get_or_create_ai_user():
    ai_user = db_session.query(User).filter_by(username="ai_assistant").first()
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
    db_session.add(ai_user)
    db_session.commit()
    db_session.refresh(ai_user)
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all messages for current user"""
    messages = (
        db_session.query(Messages)
        .filter(
            (Messages.sender_id == current_user.id) |
            (Messages.receiver_id == current_user.id)
        )
        .order_by(Messages.timestamp.desc())
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
    ai_user = get_or_create_ai_user()

    ai_messages = (
        db_session.query(Messages)
        .filter(
            ((Messages.sender_id == current_user.id) & (Messages.receiver_id == ai_user.id)) |
            ((Messages.sender_id == ai_user.id) & (Messages.receiver_id == current_user.id))
        )
        .order_by(Messages.timestamp.asc(), Messages.id.asc())
        .all()
    )

    legacy_messages = (
        db_session.query(Messages)
        .filter(
            Messages.sender_id == current_user.id,
            Messages.receiver_id == current_user.id
        )
        .order_by(Messages.timestamp.asc(), Messages.id.asc())
        .all()
    )

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


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread messages"""
    count = (
        db_session.query(Messages)
        .filter_by(receiver_id=current_user.id, is_read=False)
        .count()
    )
    return {"unread": count}

@router.post("", response_model=dict)
async def send_message(
        data: MessageCreate,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Send a message - AI responds if sending to ai_assistant"""

    if data.receiver_username == "ai_assistant":
        receiver = get_or_create_ai_user()
    else:
        receiver = db_session.query(User).filter_by(username=data.receiver_username).first()
        if not receiver:
            raise HTTPException(404, "Receiver not found")

    # Store user's message
    user_msg = Messages(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=data.content,
        is_read=data.receiver_username == "ai_assistant",
    )
    db_session.add(user_msg)
    db_session.commit()
    db_session.refresh(user_msg)
    log_activity(
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
        ai_response = ai_chat.respond(db_session, current_user, data.content)

        ai_msg = Messages(
            sender_id=receiver.id,
            receiver_id=current_user.id,
            content=ai_response,
        )
        db_session.add(ai_msg)
        db_session.commit()
        db_session.refresh(ai_msg)
        log_activity(
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
    log_activity(
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
    msg = db_session.query(Messages).get(message_id)
    if not msg or msg.receiver_id != current_user.id:
        raise HTTPException(404, "Message not found")
    if msg.status == "sent":
        msg.status = "delivered"
        msg.delivered_at = datetime.utcnow()
        db_session.commit()
    return {"status": msg.status}


@router.put("/{message_id}/read")
def mark_read(
        message_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Mark message as read"""
    msg = db_session.query(Messages).get(message_id)
    if not msg or msg.receiver_id != current_user.id:
        raise HTTPException(404, "Message not found")
    if msg.status in ("sent", "delivered"):
        msg.status = "read"
    msg.is_read = True
    msg.read_at = datetime.utcnow()
    db_session.commit()
    return {"status": msg.status, "read_at": msg.read_at.isoformat() if msg.read_at else None}


@router.put("/{message_id}/edit")
def edit_message(
        message_id: int,
        data: MessageEdit,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Edit a sent message"""
    msg = db_session.query(Messages).get(message_id)
    if not msg or msg.sender_id != current_user.id:
        raise HTTPException(404, "Message not found")
    if msg.is_deleted:
        raise HTTPException(400, "Cannot edit deleted message")

    msg.content = data.content
    msg.is_edited = True
    msg.edited_at = datetime.utcnow()
    db_session.commit()
    return {"message": "Message edited", "edited_at": msg.edited_at.isoformat()}


@router.delete("/{message_id}")
def delete_message(
        message_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Soft delete a message"""
    msg = db_session.query(Messages).get(message_id)
    if not msg or msg.sender_id != current_user.id:
        raise HTTPException(404, "Message not found")

    msg.is_deleted = True
    msg.deleted_at = datetime.utcnow()
    db_session.commit()
    return {"message": "Message deleted"}


@router.post("/{message_id}/forward")
def forward_message(
        message_id: int,
        data: ForwardRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Forward a message to another user"""
    original = db_session.query(Messages).get(message_id)
    if not original:
        raise HTTPException(404, "Message not found")

    receiver = db_session.query(User).filter_by(username=data.receiver_username).first()
    if not receiver:
        raise HTTPException(404, "Receiver not found")

    forwarded = Messages(
        sender_id=current_user.id,
        receiver_id=receiver.id,
        content=original.content,
        forwarded_from_id=original.id,
    )
    db_session.add(forwarded)
    db_session.commit()
    db_session.refresh(forwarded)
    return {"message": "Message forwarded", "id": forwarded.id}
