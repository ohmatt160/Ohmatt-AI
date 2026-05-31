# app/models/activity_log.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.extensions import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # What happened
    action = Column(String(100), nullable=False)  # login, create_transaction, connect_bank, etc.
    entity_type = Column(String(50))  # transaction, bank_account, message
    entity_id = Column(String(100))  # ID of the affected item

    # Details
    description = Column(Text)
    metadata_json = Column("metadata", JSON)  # Extra context

    # Where it happened
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    endpoint = Column(String(200))  # API endpoint called

    # Feedback specific
    feedback_type = Column(String(50))  # bug, feature_request, general
    feedback_rating = Column(Integer)  # 1-5 star rating
    feedback_status = Column(String(20), default="new")  # new, reviewed, resolved

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="activity_logs")
