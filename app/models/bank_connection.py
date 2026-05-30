from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import Base
from datetime import datetime


class BankConnection(Base):
    __tablename__ = "bank_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    provider_id = Column(Integer, ForeignKey('bank_providers.id'), nullable=False)

    # Provider-specific data
    access_token = Column(String(500))
    item_id = Column(String(200))
    institution_id = Column(String(100))
    institution_name = Column(String(200))

    # Connection metadata
    is_active = Column(Boolean, default=True)
    last_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    provider = relationship("BankProvider", back_populates="connections")
    accounts = relationship("BankAccount", back_populates="connection")
    user = relationship("User", back_populates="bank_connections")