from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, JSON, String, Text

from app.extensions import Base


class IntegrationOutbox(Base):
    __tablename__ = "integration_outbox"
    __table_args__ = (
        Index("ix_integration_outbox_dispatch", "destination", "status", "available_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    destination = Column(String(50), nullable=False, default="ohmattos")
    event_type = Column(String(100), nullable=False)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(String(100), nullable=False)
    idempotency_key = Column(String(200), nullable=False, unique=True, index=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=8)
    available_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    locked_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
