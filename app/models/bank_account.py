from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import Base
from datetime import datetime


class BankAccount(Base):
    __tablename__ = "bank_account"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Institution info
    institution_name = Column(String(100), nullable=False)
    account_name = Column(String(100), nullable=False)
    official_name = Column(String(200))
    name = Column(String(200))

    # Account info
    account_type = Column(String(50), nullable=False)  # checking, savings, credit, etc.
    type = Column(String(50))
    subtype = Column(String(50))
    account_id = Column(String(100), nullable=False)  # Provider's account ID

    # Connection info
    connection_id = Column(Integer, ForeignKey('bank_connections.id'), nullable=True)

    # Balance information
    balance_available = Column(Float, default=0.0)
    balance_current = Column(Float, default=0.0)
    balance_limit = Column(Float)
    currency = Column(String(10), default='USD')

    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="bank_accounts")
    connection = relationship("BankConnection", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account")
    account_transactions = relationship("BankTransaction", back_populates="bank_account")