from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.extensions import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
        Index("ix_transactions_user_category_date", "user_id", "category", "date"),
        Index("ix_transactions_user_account_date", "user_id", "account_id", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    date = Column(DateTime)
    ml_confidence = Column(Float, default=0.0)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('bank_account.id'))

    transaction_id = Column(String(100), unique=True)
    currency = Column(String(3), default='USD')
    datetime = Column(DateTime)
    description = Column(String(500))
    merchant_name = Column(String(200))

    category = Column(String(100))
    user_category = Column(String(100))
    subcategory = Column(String(100))

    pending = Column(Boolean, default=False)
    is_transfer = Column(Boolean, default=False)

    user = relationship("User", back_populates="transactions")
    account = relationship("BankAccount", back_populates="transactions")
