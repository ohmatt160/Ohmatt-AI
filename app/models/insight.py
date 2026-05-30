# app/models/insight.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.extensions import Base


class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Insight content
    type = Column(String(50), nullable=False)  # spending_pattern, anomaly, suggestion, forecast
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="low")  # low, medium, high

    # Related data
    category = Column(String(100), nullable=True)
    amount = Column(Float, nullable=True)
    related_transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=True)

    # Status
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="insights")
    transaction = relationship("Transaction", backref="insights")