import enum

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, String, Index
from sqlalchemy.orm import relationship
from app.extensions import Base
from datetime import datetime


class MessageStatus(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class Messages(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_receiver_read_time", "receiver_id", "is_read", "timestamp"),
        Index("ix_messages_sender_time", "sender_id", "timestamp"),
    )

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

    # Status tracking
    status = Column(String(20), default="sent")  # sent, delivered, read
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)

    # Message actions
    is_edited = Column(Boolean, default=False)
    edited_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Forward tracking
    forwarded_from_id = Column(Integer, ForeignKey('messages.id'), nullable=True)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    forwarded_from = relationship("Messages", remote_side=[id], backref="forwards")





