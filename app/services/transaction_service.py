from sqlalchemy.orm import Session
from typing import List
from app.models.transaction import Transaction
from app.services.ai_service import ai_service


class TransactionService:
    def __init__(self):
        self.ai_service = ai_service  # Use singleton

    def categorize_transaction(self, description: str) -> tuple:
        return self.ai_service.categorize_transaction(description)

    def analyze_spending(
        self,
        db: Session,
        user_id: int,
        currency: str,
    ) -> List[str]:
        return self.ai_service.analyze_spending(db, user_id, currency)

    def create_transaction_from_plaid(
            self,
            db: Session,
            plaid_transaction: dict,
            user_id: int,
            bank_account_id: int
    ) -> Transaction:
        category, confidence = self.categorize_transaction(plaid_transaction.get('name', ''))

        transaction = Transaction(
            amount=plaid_transaction.get('amount', 0.0),
            date=plaid_transaction.get('date'),
            ml_confidence=confidence,
            user_id=user_id,
            account_id=bank_account_id,
            transaction_id=plaid_transaction.get('transaction_id'),
            currency=plaid_transaction.get('iso_currency_code', 'USD'),
            datetime=plaid_transaction.get('datetime'),
            description=plaid_transaction.get('name'),
            merchant_name=plaid_transaction.get('merchant_name'),
            category=category,
            pending=plaid_transaction.get('pending', False)
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    def get_user_transactions(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100
    ) -> List[Transaction]:
        return db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).offset(skip).limit(limit).all()
