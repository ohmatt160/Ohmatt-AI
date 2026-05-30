from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from app.services.ai_service import ai_service
from app.providers.plaid_provider import PlaidProvider
from app.providers.flutterwave_provider import FlutterwaveProvider
from app.models.bank_connection import BankConnection
from app.models.bank_account import BankAccount
from app.models.bank_transaction import BankTransaction
from app.models.bank_provider import BankProvider
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


class BankingService:
    def __init__(self):
        self.ai_service = ai_service  # Use singleton

    def get_provider_for_user(self, db: Session, user_id: int) -> Optional[Any]:
        connection = db.query(BankConnection).filter(
            BankConnection.user_id == user_id,
            BankConnection.is_active == True
        ).first()

        if not connection:
            return None

        provider = db.query(BankProvider).filter(
            BankProvider.id == connection.provider_id
        ).first()

        if not provider:
            return None

        config = {
            'name': provider.name,
            'api_name': provider.api_name,
        }

        if provider.api_config:
            config.update(provider.api_config)

        if provider.api_name == 'plaid':
            config.update({
                'client_id': provider.api_config.get('client_id') if provider.api_config else None,
                'secret': provider.api_config.get('secret') if provider.api_config else None,
                'environment': provider.api_config.get('environment', 'sandbox') if provider.api_config else 'sandbox'
            })
            return PlaidProvider(config)
        elif provider.api_name == 'flutterwave':
            config.update({
                'secret_key': provider.api_config.get('secret_key') if provider.api_config else None,
                'public_key': provider.api_config.get('public_key') if provider.api_config else None,
                'encryption_key': provider.api_config.get('encryption_key') if provider.api_config else None,
                'base_url': provider.api_config.get('base_url',
                                                    'https://api.flutterwave.com/v3') if provider.api_config else 'https://api.flutterwave.com/v3'
            })
            return FlutterwaveProvider(config)
        else:
            logger.warning(f"Unsupported provider: {provider.api_name}")
            return None

    # ... rest of methods stay the same ...

    def sync_user_accounts(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """Sync bank accounts for a user"""
        provider = self.get_provider_for_user(db, user_id)
        if not provider:
            raise ValueError("No active banking provider found for user")

        # Get user's bank connection
        connection = db.query(BankConnection).filter(
            BankConnection.user_id == user_id,
            BankConnection.is_active == True
        ).first()

        if not connection or not connection.access_token:
            raise ValueError("No valid access token found for user")

        # Get accounts from provider
        accounts_data = provider.get_accounts(connection.access_token)

        # Update or create bank accounts in database
        synced_accounts = []
        for account_data in accounts_data:
            # Check if account already exists
            existing_account = db.query(BankAccount).filter(
                BankAccount.account_id == account_data['account_id'],
                BankAccount.user_id == user_id
            ).first()

            if existing_account:
                # Update existing account
                existing_account.balance_available = account_data['balances']['available']
                existing_account.balance_current = account_data['balances']['current']
                existing_account.balance_limit = account_data['balances']['limit']
                existing_account.currency = account_data['balances']['currency']
                existing_account.last_updated = datetime.utcnow()
                db.add(existing_account)
                synced_accounts.append(existing_account)
            else:
                # Create new account
                new_account = BankAccount(
                    user_id=user_id,
                    connection_id=connection.id,
                    institution_name=account_data.get('official_name', ''),
                    account_name=account_data['name'],
                    official_name=account_data.get('official_name', ''),
                    name=account_data['name'],
                    account_type=account_data['type'],
                    type=account_data['type'],
                    subtype=account_data.get('subtype', ''),
                    account_id=account_data['account_id'],
                    balance_available=account_data['balances']['available'],
                    balance_current=account_data['balances']['current'],
                    balance_limit=account_data['balances']['limit'],
                    currency=account_data['balances']['currency'],
                    is_active=True
                )
                db.add(new_account)
                synced_accounts.append(new_account)

        db.commit()

        # Refresh objects to get IDs
        for account in synced_accounts:
            db.refresh(account)

        return synced_accounts

    def sync_user_transactions(
        self,
        db: Session,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Transaction]:
        """Sync transactions for a user"""
        provider = self.get_provider_for_user(db, user_id)
        if not provider:
            raise ValueError("No active banking provider found for user")

        # Get user's bank connection
        connection = db.query(BankConnection).filter(
            BankConnection.user_id == user_id,
            BankConnection.is_active == True
        ).first()

        if not connection or not connection.access_token:
            raise ValueError("No valid access token found for user")

        # Set default date range if not provided (last 30 days)
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')

        # Get user's bank accounts
        accounts = db.query(BankAccount).filter(
            BankAccount.user_id == user_id,
            BankAccount.is_active == True
        ).all()

        account_ids = [account.account_id for account in accounts]

        # Get transactions from provider
        transactions_data = provider.get_transactions(
            connection.access_token,
            start_date,
            end_date,
            account_ids if account_ids else None
        )

        # Create transaction objects
        synced_transactions = []
        for txn_data in transactions_data:
            # Check if transaction already exists (by transaction_id)
            existing_transaction = db.query(Transaction).filter(
                Transaction.transaction_id == txn_data['transaction_id']
            ).first()

            if existing_transaction:
                continue  # Skip existing transaction

            # Categorize transaction using AI
            category, confidence = self.ai_service.categorize_transaction(txn_data.get('name', ''))

            # Find the bank account for this transaction
            bank_account = None
            for account in accounts:
                if account.account_id == txn_data['account_id']:
                    bank_account = account
                    break

            if not bank_account:
                logger.warning(f"No bank account found for account_id: {txn_data['account_id']}")
                continue

            # Create transaction
            transaction = Transaction(
                amount=txn_data['amount'],
                date=txn_data['date'],
                ml_confidence=confidence,
                user_id=user_id,
                account_id=bank_account.id,
                transaction_id=txn_data['transaction_id'],
                currency=txn_data.get('currency', 'USD'),
                datetime=txn_data['date'],
                description=txn_data['name'],
                merchant_name=txn_data.get('merchant_name'),
                category=category,
                pending=txn_data.get('pending', False)
            )

            db.add(transaction)
            synced_transactions.append(transaction)

        db.commit()

        # Refresh objects to get IDs
        for transaction in synced_transactions:
            db.refresh(transaction)

        return synced_transactions

    def get_user_bank_accounts(self, db: Session, user_id: int) -> List[BankAccount]:
        """Get all bank accounts for a user"""
        return db.query(BankAccount).filter(
            BankAccount.user_id == user_id,
            BankAccount.is_active == True
        ).all()

    def get_user_bank_transactions(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[BankTransaction]:
        """Get bank transactions for a user"""
        return db.query(BankTransaction).filter(
            BankTransaction.user_id == user_id
        ).offset(skip).limit(limit).all()