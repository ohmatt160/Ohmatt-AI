from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.extensions import Base
from datetime import datetime


class BankTransaction(Base):
    __tablename__ = "bank_transaction"
    __table_args__ = (
        Index("ix_bank_transactions_user_date", "user_id", "date"),
        Index("ix_bank_transactions_account_date", "bank_account_id", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    bank_account_id = Column(Integer, ForeignKey('bank_account.id'))

    # Transaction info
    transaction_id = Column(String(100), unique=True)  # Provider's transaction ID
    description = Column(String(255), nullable=False)
    # amount = Column(Numeric(15, 2), nullable=False)
    date = Column(DateTime, nullable=False)

    # Categorization
    category = Column(String(100))
    merchant_name = Column(String(100))

    # Status
    pending = Column(Boolean, default=False)
    currency = Column(String(10), default='USD')

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_bank_transactions")
    bank_account = relationship("BankAccount", back_populates="account_transactions")
    amount = Column(Float, nullable=False)
