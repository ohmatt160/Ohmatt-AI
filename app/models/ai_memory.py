from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint

from app.extensions import Base


class AIPersonalMemory(Base):
    __tablename__ = "ai_personal_memories"
    __table_args__ = (
        Index("ix_ai_personal_memories_user_created", "user_id", "created_at", "id"),
        UniqueConstraint("user_id", "content", name="uq_ai_personal_memory_user_content"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
