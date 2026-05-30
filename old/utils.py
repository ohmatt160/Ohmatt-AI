import base64
import hashlib
import hmac
from datetime import datetime
from functools import wraps

from plaid import ApiClient, Configuration
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from sqlalchemy.orm import sessionmaker
from ai_module import categorize_transaction, analyze_spending
from config import serializer, mail,app
from model import User, Activity,  db, Transaction
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import create_engine
from flask_mail import Message
from flask import request, jsonify
from typing import Dict, List, Optional, Type
import json,requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod



class BankingProvider(ABC):
    """Abstract base class for all banking providers"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'Unknown')
        self.api_name = config.get('api_name', '')

    @abstractmethod
    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create a link token or auth URL for connecting bank account"""
        pass

    @abstractmethod
    def exchange_token(self, public_token: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange public token for access token"""
        pass

    @abstractmethod
    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's bank accounts"""
        pass

    @abstractmethod
    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get transactions for accounts"""
        pass

    @abstractmethod
    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get account balances"""
        pass

    @abstractmethod
    def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """Get institution information"""
        pass

    def health_check(self) -> Dict[str, Any]:
        """Check if provider API is healthy"""
        return {
            'provider': self.api_name,
            'status': 'unknown',
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_capabilities(self) -> List[str]:
        """Get provider capabilities"""
        return ['basic']


class PlaidProvider(BankingProvider):
    """Plaid banking provider for US/Canada/Europe"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Configure Plaid
        plaid_env = config.get('environment', 'sandbox')
        plaid_hosts = {
            'sandbox': 'https://sandbox.plaid.com',
            'development': 'https://development.plaid.com',
            'production': 'https://production.plaid.com'
        }

        host = plaid_hosts.get(plaid_env, 'https://sandbox.plaid.com')

        self.configuration = Configuration(
            host=host,
            api_key={
                "clientId": config.get('client_id'),
                "secret": config.get('secret'),
            }
        )

        self.api_client = ApiClient(self.configuration)
        self.client = plaid_api.PlaidApi(self.api_client)

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create Plaid link token"""
        try:
            # Map country code to Plaid's country code
            country_map = {
                'US': CountryCode('US'),
                'CA': CountryCode('CA'),
                'GB': CountryCode('GB'),
                'IE': CountryCode('IE'),
                'ES': CountryCode('ES'),
                'FR': CountryCode('FR'),
                'DE': CountryCode('DE'),
                'NL': CountryCode('NL'),
            }

            plaid_country = country_map.get(country_code.upper(), CountryCode('US'))

            # Determine products based on country
            if country_code.upper() == 'US':
                products = [Products("transactions"), Products("auth")]
            else:
                products = [Products("transactions")]

            request = LinkTokenCreateRequest(
                user={"client_user_id": str(user_id)},
                client_name="Oh-Matt Finance AI",
                products=products,
                country_codes=[plaid_country],
                language='en',
                redirect_uri=self.config.get('redirect_uri', ''),
                webhook=self.config.get('webhook_url', '')
            )

            response = self.client.link_token_create(request)

            return {
                'link_token': response.link_token,
                'expiration': response.expiration,
                'request_id': response.request_id,
                'provider': 'plaid'
            }

        except Exception as e:
            return {
                'error': str(e),
                'provider': 'plaid'
            }

    def exchange_token(self, public_token: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange Plaid public token for access token"""
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)

            return {
                'access_token': response.access_token,
                'item_id': response.item_id,
                'request_id': response.request_id,
                'provider': 'plaid'
            }

        except Exception as e:
            return {
                'error': str(e),
                'provider': 'plaid'
            }

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get Plaid accounts"""
        try:
            response = self.client.accounts_get({
                'access_token': access_token
            })

            accounts = []
            for account in response.accounts:
                accounts.append({
                    'account_id': account.account_id,
                    'name': account.name,
                    'official_name': account.official_name,
                    'type': account.type,
                    'subtype': account.subtype,
                    'balances': {
                        'available': account.balances.available,
                        'current': account.balances.current,
                        'limit': account.balances.limit,
                        'currency': account.balances.iso_currency_code
                    }
                })

            return accounts

        except Exception as e:
            print(f"Error getting Plaid accounts: {e}")
            return []

    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get Plaid transactions"""
        try:
            response = self.client.transactions_get({
                'access_token': access_token,
                'start_date': start_date,
                'end_date': end_date,
                'options': {
                    'account_ids': account_ids
                } if account_ids else {}
            })

            transactions = []
            for txn in response.transactions:
                transactions.append({
                    'transaction_id': txn.transaction_id,
                    'account_id': txn.account_id,
                    'amount': txn.amount,
                    'date': txn.date,
                    'name': txn.name,
                    'merchant_name': txn.merchant_name,
                    'category': txn.category,
                    'pending': txn.pending
                })

            return transactions

        except Exception as e:
            print(f"Error getting Plaid transactions: {e}")
            return []

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get Plaid balances"""
        try:
            response = self.client.accounts_get({
                'access_token': access_token
            })

            balances = []
            for account in response.accounts:
                if account_ids and account.account_id not in account_ids:
                    continue

                balances.append({
                    'account_id': account.account_id,
                    'balances': {
                        'available': account.balances.available,
                        'current': account.balances.current,
                        'limit': account.balances.limit,
                        'currency': account.balances.iso_currency_code
                    },
                    'name': account.name
                })

            return balances

        except Exception as e:
            print(f"Error getting Plaid balances: {e}")
            return []

    def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """Get Plaid institution info"""
        try:
            response = self.client.institutions_get_by_id({
                'institution_id': institution_id,
                'country_codes': [CountryCode('US')]
            })

            institution = response.institution
            return {
                'institution_id': institution.institution_id,
                'name': institution.name,
                'products': institution.products,
                'country_codes': institution.country_codes,
                'url': institution.url,
                'logo': institution.logo
            }

        except Exception as e:
            print(f"Error getting Plaid institution: {e}")
            return {
                'name': 'Unknown Institution',
                'institution_id': institution_id
            }

    def health_check(self) -> Dict[str, Any]:
        """Check Plaid API health"""
        try:
            # Simple health check - try to get institutions
            self.client.institutions_get({
                'count': 1,
                'offset': 0,
                'country_codes': [CountryCode('US')]
            })

            return {
                'provider': 'plaid',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'provider': 'plaid',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_capabilities(self) -> List[str]:
        """Get Plaid capabilities"""
        return ['transactions', 'balances', 'auth', 'identity', 'investments']

class FlutterwaveProvider(BankingProvider):
    """Flutterwave banking provider for Africa"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key')
        self.encryption_key = config.get('encryption_key')
        self.base_url = config.get('base_url', 'https://api.flutterwave.com/v3')

        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create Flutterwave bank connection link"""
        # For Flutterwave, we typically redirect to their OAuth flow
        # or use account verification endpoints

        # Generate a unique reference
        import uuid
        tx_ref = f"oh-matt-finance-{user_id}-{uuid.uuid4().hex[:8]}"

        # Create redirect URL for OAuth
        redirect_url = f"https://your-app.com/banking/callback/flutterwave"

        # Depending on country, use appropriate bank connection method
        if country_code == 'NG':
            # Nigeria - use Bank Account Verification or Transfers
            return {
                'provider': 'flutterwave',
                'country': country_code,
                'auth_type': 'account_verification',
                'tx_ref': tx_ref,
                'note': 'For Nigeria, use account verification or transfers API'
            }
        else:
            # Other African countries - use OAuth where available
            return {
                'provider': 'flutterwave',
                'country': country_code,
                'auth_type': 'oauth_redirect',
                'redirect_url': f"{self.base_url}/oauth/authorize",
                'tx_ref': tx_ref,
                'scopes': ['read', 'transactions']
            }

    def exchange_token(self, authorization_code: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        # Flutterwave OAuth token exchange
        token_url = f"{self.base_url}/oauth/token"

        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'client_id': self.public_key,
            'client_secret': self.secret_key,
            'redirect_uri': metadata.get('redirect_uri')
        }

        response = requests.post(token_url, json=data, headers=self.headers)
        response.raise_for_status()

        token_data = response.json()

        return {
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_in': token_data.get('expires_in'),
            'provider': 'flutterwave'
        }

    def verify_bank_account(self, account_number: str, bank_code: str, country: str = 'NG') -> Dict[str, Any]:
        """Verify Nigerian bank account (Flutterwave's strength)"""
        url = f"{self.base_url}/accounts/resolve"

        data = {
            'account_number': account_number,
            'account_bank': bank_code
        }

        response = requests.post(url, json=data, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'account_number': result['data']['account_number'],
                'account_name': result['data']['account_name'],
                'bank_code': bank_code,
                'country': country
            }
        else:
            return {
                'success': False,
                'error': response.json().get('message', 'Verification failed')
            }

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get bank accounts connected via OAuth"""
        # Note: Flutterwave's OAuth for bank accounts might be limited
        # Most African APIs focus on payments/transfers, not full account access

        # For now, return empty or use alternative methods
        return []

    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get transactions - might use transfers API for African context"""
        # African providers often don't provide full transaction history API
        # We might need to track transactions via webhooks or transfers

        # For Flutterwave, we can get transfer history
        url = f"{self.base_url}/transfers"
        params = {
            'from': start_date,
            'to': end_date,
            'status': 'successful'
        }

        response = requests.get(url, headers=self.headers, params=params)

        transactions = []
        if response.status_code == 200:
            data = response.json()
            for transfer in data.get('data', []):
                transactions.append({
                    'transaction_id': transfer.get('id'),
                    'amount': transfer.get('amount'),
                    'currency': transfer.get('currency'),
                    'narration': transfer.get('narration'),
                    'reference': transfer.get('reference'),
                    'status': transfer.get('status'),
                    'date': transfer.get('created_at'),
                    'type': 'transfer',
                    'provider': 'flutterwave'
                })

        return transactions

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get balances - might use wallet/balance API"""
        url = f"{self.base_url}/balances"

        response = requests.get(url, headers=self.headers)

        balances = []
        if response.status_code == 200:
            data = response.json()
            for balance in data.get('data', []):
                balances.append({
                    'currency': balance.get('currency'),
                    'available_balance': balance.get('available_balance'),
                    'ledger_balance': balance.get('ledger_balance'),
                    'provider': 'flutterwave'
                })

        return balances

    def create_transfer(self, account_bank: str, account_number: str,
                        amount: float, currency: str, narration: str) -> Dict[str, Any]:
        """Create bank transfer (common in African fintech)"""
        url = f"{self.base_url}/transfers"

        import uuid
        data = {
            'account_bank': account_bank,
            'account_number': account_number,
            'amount': amount,
            'currency': currency,
            'narration': narration,
            'reference': f"transfer-{uuid.uuid4().hex[:10]}",
            'callback_url': 'https://your-webhook-url.com/flutterwave'
        }

        response = requests.post(url, json=data, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            return {
                'success': True,
                'transfer_id': result['data']['id'],
                'reference': result['data']['reference'],
                'status': result['data']['status']
            }
        else:
            return {
                'success': False,
                'error': response.json().get('message', 'Transfer failed')
            }

    def get_institution(self, bank_code: str) -> Dict[str, Any]:
        """Get bank/institution information"""
        url = f"{self.base_url}/banks/{bank_code}"

        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            data = response.json()
            return {
                'code': data['data']['code'],
                'name': data['data']['name'],
                'country': data['data'].get('country', 'NG')
            }

        return {
            'name': 'Unknown Bank',
            'code': bank_code
        }


class PaystackProvider(BankingProvider):
    """Paystack banking provider for Nigeria and Ghana"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key')
        self.base_url = config.get('base_url', 'https://api.paystack.co')

        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Paystack uses account verification, not OAuth"""
        return {
            'provider': 'paystack',
            'method': 'account_verification',
            'country': country_code,
            'instructions': 'Use /verify-account endpoint with account number and bank code'
        }

    def exchange_token(self, authorization_code: str, metadata: Dict) -> Dict[str, Any]:
        """Paystack doesn't use OAuth tokens"""
        return {
            'provider': 'paystack',
            'note': 'Paystack uses API key authentication',
            'method': 'api_key_based'
        }

    def resolve_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """Resolve Nigerian/Ghanaian bank account details"""
        url = f"{self.base_url}/bank/resolve"

        params = {
            'account_number': account_number,
            'bank_code': bank_code
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()

            if data.get('status'):
                return {
                    'success': True,
                    'account_number': data['data']['account_number'],
                    'account_name': data['data']['account_name'],
                    'bank_id': data['data']['bank_id'],
                    'provider': 'paystack'
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Account resolution failed'),
                    'provider': 'paystack'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'paystack'
            }

    def list_banks(self, country: str = 'nigeria') -> List[Dict[str, Any]]:
        """List supported banks"""
        url = f"{self.base_url}/bank"
        params = {'country': country} if country else {}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()

            banks = []
            if data.get('status'):
                for bank in data['data']:
                    banks.append({
                        'code': bank['code'],
                        'name': bank['name'],
                        'slug': bank['slug'],
                        'country': bank.get('country', 'nigeria')
                    })
            return banks

        except Exception as e:
            print(f"Error listing banks: {e}")
            return []

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Paystack doesn't provide bank account access like Plaid"""
        return []

    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get Paystack transactions (payment transactions)"""
        url = f"{self.base_url}/transaction"

        params = {
            'from': start_date,
            'to': end_date,
            'perPage': 100
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()

            transactions = []
            if data.get('status'):
                for txn in data['data']:
                    transactions.append({
                        'transaction_id': txn.get('id'),
                        'reference': txn.get('reference'),
                        'amount': txn.get('amount') / 100 if txn.get('amount') else 0,
                        'currency': txn.get('currency', 'NGN'),
                        'status': txn.get('status'),
                        'channel': txn.get('channel'),
                        'paid_at': txn.get('paid_at'),
                        'customer': txn.get('customer', {}),
                        'provider': 'paystack'
                    })

            return transactions

        except Exception as e:
            print(f"Error getting transactions: {e}")
            return []

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get Paystack balance"""
        url = f"{self.base_url}/balance"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            balances = []
            if data.get('status'):
                for balance in data['data']:
                    balances.append({
                        'currency': balance.get('currency'),
                        'balance': balance.get('balance') / 100 if balance.get('balance') else 0,
                        'provider': 'paystack'
                    })

            return balances

        except Exception as e:
            print(f"Error getting balances: {e}")
            return []

    def get_institution(self, bank_code: str) -> Dict[str, Any]:
        """Get bank information"""
        banks = self.list_banks()

        for bank in banks:
            if bank['code'] == bank_code:
                return {
                    'name': bank['name'],
                    'code': bank['code'],
                    'country': bank.get('country', 'nigeria'),
                    'provider': 'paystack'
                }

        return {
            'name': 'Unknown Bank',
            'code': bank_code,
            'provider': 'paystack'
        }

    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify Paystack webhook signature"""
        computed_signature = hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature)

    def process_webhook(self, payload: Dict) -> Dict[str, Any]:
        """Process Paystack webhook data"""
        event = payload.get('event')
        data = payload.get('data', {})

        return {
            'provider': 'paystack',
            'event': event,
            'transaction_id': data.get('id'),
            'reference': data.get('reference'),
            'amount': data.get('amount', 0) / 100 if data.get('amount') else 0,
            'currency': data.get('currency', 'NGN'),
            'status': data.get('status'),
            'customer': data.get('customer', {}),
            'authorization': data.get('authorization', {})
        }

    def health_check(self) -> Dict[str, Any]:
        """Check Paystack API health"""
        try:
            response = requests.get(f"{self.base_url}/bank", headers=self.headers)

            if response.status_code == 200:
                return {
                    'provider': 'paystack',
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'provider': 'paystack',
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'provider': 'paystack',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_capabilities(self) -> List[str]:
        """Get Paystack capabilities"""
        return ['account_verification', 'payments', 'subscriptions', 'transfers']


class MonoProvider(BankingProvider):
    """Mono banking provider for Nigeria"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key')
        self.base_url = config.get('base_url', 'https://api.withmono.com')

        self.headers = {
            'Content-Type': 'application/json',
            'mono-sec-key': self.secret_key
        }

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create Mono connect widget token"""
        url = f"{self.base_url}/account/auth"

        # Generate reference for this user
        reference = f"ohmatt_{user_id}_{datetime.utcnow().timestamp()}"

        payload = {
            'reference': reference,
            'success_url': 'https://yourapp.com/banking/callback/mono/success',
            'webhook_url': 'https://yourapp.com/webhooks/mono'
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if 'token' in data:
                return {
                    'provider': 'mono',
                    'method': 'connect_widget',
                    'token': data['token'],
                    'reference': reference,
                    'country': 'NG',
                    'widget_url': 'https://connect.withmono.com',  # Mono connect widget
                    'instructions': 'Embed the Mono connect widget with this token'
                }
            else:
                return {
                    'provider': 'mono',
                    'error': data.get('message', 'Failed to create token'),
                    'country': 'NG'
                }

        except Exception as e:
            return {
                'provider': 'mono',
                'error': str(e),
                'country': 'NG'
            }

    def exchange_token(self, code: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange Mono code for account ID"""
        url = f"{self.base_url}/account/auth"

        payload = {
            'code': code
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if 'id' in data:
                return {
                    'account_id': data['id'],
                    'provider': 'mono',
                    'status': 'success'
                }
            else:
                return {
                    'error': data.get('message', 'Failed to exchange token'),
                    'provider': 'mono'
                }

        except Exception as e:
            return {
                'error': str(e),
                'provider': 'mono'
            }

    def get_accounts(self, account_id: str) -> List[Dict[str, Any]]:
        """Get Mono account information"""
        url = f"{self.base_url}/accounts/{account_id}"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if 'account' in data:
                account = data['account']
                return [{
                    'account_id': account_id,
                    'institution': {
                        'name': account.get('institution', {}).get('name'),
                        'bank_code': account.get('institution', {}).get('bankCode'),
                        'type': account.get('institution', {}).get('type')
                    },
                    'account_number': account.get('accountNumber'),
                    'account_name': account.get('name'),
                    'balance': account.get('balance'),
                    'currency': account.get('currency', 'NGN'),
                    'type': account.get('type'),
                    'bvn': account.get('bvn'),
                    'provider': 'mono'
                }]
            else:
                return []

        except Exception as e:
            print(f"Error getting Mono account: {e}")
            return []

    def get_transactions(self, account_id: str,
                         start_date: str = None,
                         end_date: str = None,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get Mono transactions"""
        url = f"{self.base_url}/accounts/{account_id}/transactions"

        params = {}
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date

        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()

            transactions = []
            if 'data' in data:
                for txn in data['data']:
                    transactions.append({
                        'transaction_id': txn.get('_id'),
                        'amount': txn.get('amount'),
                        'currency': txn.get('currency', 'NGN'),
                        'narration': txn.get('narration'),
                        'type': txn.get('type'),
                        'category': txn.get('category'),
                        'balance': txn.get('balance'),
                        'date': txn.get('date'),
                        'account_id': account_id,
                        'provider': 'mono'
                    })

            return transactions

        except Exception as e:
            print(f"Error getting Mono transactions: {e}")
            return []

    def get_income(self, account_id: str) -> Dict[str, Any]:
        """Get income insights (Mono's unique feature)"""
        url = f"{self.base_url}/accounts/{account_id}/income"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            return {
                'account_id': account_id,
                'income_data': data.get('data', {}),
                'provider': 'mono'
            }

        except Exception as e:
            print(f"Error getting Mono income: {e}")
            return {}

    def get_identity(self, account_id: str) -> Dict[str, Any]:
        """Get identity information (Mono's unique feature)"""
        url = f"{self.base_url}/accounts/{account_id}/identity"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if 'data' in data:
                identity = data['data']
                return {
                    'account_id': account_id,
                    'identity': {
                        'name': identity.get('name'),
                        'email': identity.get('email'),
                        'phone': identity.get('phone'),
                        'gender': identity.get('gender'),
                        'address': identity.get('address'),
                        'birthday': identity.get('birthday'),
                        'bvn': identity.get('bvn')
                    },
                    'provider': 'mono'
                }
            else:
                return {}

        except Exception as e:
            print(f"Error getting Mono identity: {e}")
            return {}

    def get_balances(self, account_id: str) -> List[Dict[str, Any]]:
        """Get Mono account balance"""
        accounts = self.get_accounts(account_id)

        balances = []
        for account in accounts:
            balances.append({
                'account_id': account_id,
                'balance': account.get('balance'),
                'currency': account.get('currency', 'NGN'),
                'provider': 'mono'
            })

        return balances

    def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """Get institution information"""
        # Mono doesn't have institution lookup API
        return {
            'name': 'Nigerian Bank',
            'provider': 'mono',
            'country': 'NG'
        }

    def sync_data(self, account_id: str) -> Dict[str, Any]:
        """Manually sync account data"""
        url = f"{self.base_url}/accounts/{account_id}/sync"

        try:
            response = requests.post(url, headers=self.headers)
            data = response.json()

            return {
                'account_id': account_id,
                'status': data.get('status'),
                'message': data.get('message'),
                'provider': 'mono'
            }

        except Exception as e:
            return {
                'account_id': account_id,
                'error': str(e),
                'provider': 'mono'
            }

    def unlink_account(self, account_id: str) -> Dict[str, Any]:
        """Unlink (reauthorize) Mono account"""
        url = f"{self.base_url}/accounts/{account_id}/unlink"

        try:
            response = requests.post(url, headers=self.headers)
            data = response.json()

            return {
                'account_id': account_id,
                'status': data.get('status'),
                'message': data.get('message'),
                'provider': 'mono'
            }

        except Exception as e:
            return {
                'account_id': account_id,
                'error': str(e),
                'provider': 'mono'
            }

    def health_check(self) -> Dict[str, Any]:
        """Check Mono API health"""
        try:
            # Try to ping the API
            response = requests.get(f"{self.base_url}/ping", headers=self.headers)

            if response.status_code == 200:
                return {
                    'provider': 'mono',
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'provider': 'mono',
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'provider': 'mono',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_capabilities(self) -> List[str]:
        """Get Mono capabilities"""
        return ['transactions', 'balance', 'income_insights', 'identity', 'account_linking']





class StitchProvider(BankingProvider):
    """Stitch banking provider for South Africa"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        self.base_url = config.get('base_url', 'https://api.stitch.money')

        # Get access token
        self.access_token = self._get_access_token()

        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def _get_access_token(self) -> str:
        """Get Stitch access token"""
        token_url = f"{self.base_url}/connect/token"

        auth_string = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'client_credentials',
            'scope': 'client_paymentrequest'
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            data = response.json()

            return data['access_token']

        except Exception as e:
            print(f"Error getting Stitch access token: {e}")
            return ''

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create Stitch payment request (South Africa uses payment initiation)"""
        # In South Africa, open banking often works through payment initiation
        # Users authorize payments and we get limited account info

        url = f"{self.base_url}/api/paymentinitiation-requests"

        import uuid
        reference = str(uuid.uuid4())

        payload = {
            'amount': {
                'quantity': '1.00',  # Minimal amount for authorization
                'currency': 'ZAR'
            },
            'payerReference': f"user_{user_id}",
            'beneficiaryReference': 'ohmatt_finance',
            'externalReference': reference,
            'beneficiaryName': 'Oh-Matt Finance',
            'beneficiaryBankId': 'fnb',  # First National Bank as example
            'beneficiaryAccountNumber': 'your_business_account_number',
            'merchant': {
                'name': 'Oh-Matt Finance AI',
                'url': 'https://ohmatt.com'
            },
            'callbackUrl': f'{self.redirect_uri}?reference={reference}'
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if 'paymentInitiationRequest' in data:
                request_data = data['paymentInitiationRequest']
                return {
                    'provider': 'stitch',
                    'method': 'payment_initiation',
                    'request_id': request_data.get('id'),
                    'url': request_data.get('url'),  # URL user visits to authorize
                    'reference': reference,
                    'country': 'ZA',
                    'currency': 'ZAR',
                    'amount': '1.00',
                    'note': 'User authorizes a small payment to verify account ownership'
                }
            else:
                return {
                    'provider': 'stitch',
                    'error': data.get('error_description', 'Failed to create payment request'),
                    'country': 'ZA'
                }

        except Exception as e:
            return {
                'provider': 'stitch',
                'error': str(e),
                'country': 'ZA'
            }

    def exchange_token(self, code: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange authorization code for user token"""
        token_url = f"{self.base_url}/connect/token"

        auth_string = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            data = response.json()

            return {
                'access_token': data.get('access_token'),
                'refresh_token': data.get('refresh_token'),
                'expires_in': data.get('expires_in'),
                'provider': 'stitch'
            }

        except Exception as e:
            return {
                'error': str(e),
                'provider': 'stitch'
            }

    def get_payment_status(self, request_id: str) -> Dict[str, Any]:
        """Get payment initiation request status"""
        url = f"{self.base_url}/api/paymentinitiation-requests/{request_id}"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if 'paymentInitiationRequest' in data:
                request_data = data['paymentInitiationRequest']
                return {
                    'request_id': request_id,
                    'status': request_data.get('status'),
                    'payer': request_data.get('payer'),
                    'amount': request_data.get('amount'),
                    'provider': 'stitch'
                }
            else:
                return {
                    'request_id': request_id,
                    'error': 'Request not found',
                    'provider': 'stitch'
                }

        except Exception as e:
            return {
                'request_id': request_id,
                'error': str(e),
                'provider': 'stitch'
            }

    def get_accounts(self, user_token: str = None) -> List[Dict[str, Any]]:
        """Get user accounts (limited in South African open banking)"""
        # Note: South African open banking APIs often don't provide full account access
        # like Plaid does. We typically get limited info through payment initiation.

        if not user_token:
            return []

        headers = {
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json'
        }

        # This endpoint might not exist in all implementations
        url = f"{self.base_url}/api/accounts"

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                accounts = []

                for account in data.get('accounts', []):
                    accounts.append({
                        'account_id': account.get('id'),
                        'account_number': account.get('accountNumber'),
                        'account_name': account.get('accountName'),
                        'bank': account.get('bank'),
                        'type': account.get('type'),
                        'currency': account.get('currency', 'ZAR'),
                        'provider': 'stitch'
                    })

                return accounts
            else:
                return []

        except Exception as e:
            print(f"Error getting Stitch accounts: {e}")
            return []

    def get_transactions(self, user_token: str = None,
                         start_date: str = None,
                         end_date: str = None,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get transactions (limited availability)"""
        # Transaction access is very limited in South African open banking
        return []

    def get_balances(self, user_token: str = None) -> List[Dict[str, Any]]:
        """Get balances (limited availability)"""
        return []

    def create_payout(self, account_number: str, bank_code: str,
                      amount: float, reference: str) -> Dict[str, Any]:
        """Create a payout (common in South African fintech)"""
        url = f"{self.base_url}/api/payouts"

        payload = {
            'amount': {
                'quantity': str(amount),
                'currency': 'ZAR'
            },
            'beneficiaryReference': reference,
            'beneficiaryName': 'User Payout',
            'beneficiaryBankId': bank_code,
            'beneficiaryAccountNumber': account_number,
            'externalReference': f"payout_{reference}",
            'merchant': {
                'name': 'Oh-Matt Finance AI'
            }
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if 'payout' in data:
                payout_data = data['payout']
                return {
                    'success': True,
                    'payout_id': payout_data.get('id'),
                    'status': payout_data.get('status'),
                    'reference': reference,
                    'provider': 'stitch'
                }
            else:
                return {
                    'success': False,
                    'error': data.get('error_description', 'Payout failed'),
                    'provider': 'stitch'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'stitch'
            }

    def get_banks(self) -> List[Dict[str, Any]]:
        """Get list of supported banks in South Africa"""
        url = f"{self.base_url}/api/banks"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            banks = []
            for bank in data.get('banks', []):
                banks.append({
                    'id': bank.get('id'),
                    'name': bank.get('name'),
                    'logo': bank.get('logo'),
                    'country': 'ZA',
                    'provider': 'stitch'
                })

            return banks

        except Exception as e:
            print(f"Error getting Stitch banks: {e}")
            return []

    def get_institution(self, bank_id: str) -> Dict[str, Any]:
        """Get bank/institution information"""
        banks = self.get_banks()

        for bank in banks:
            if bank['id'] == bank_id:
                return {
                    'id': bank_id,
                    'name': bank['name'],
                    'logo': bank.get('logo'),
                    'country': 'ZA',
                    'provider': 'stitch'
                }

        return {
            'name': 'South African Bank',
            'id': bank_id,
            'country': 'ZA',
            'provider': 'stitch'
        }

    def health_check(self) -> Dict[str, Any]:
        """Check Stitch API health"""
        try:
            response = requests.get(f"{self.base_url}/ping", headers=self.headers)

            if response.status_code == 200:
                return {
                    'provider': 'stitch',
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'provider': 'stitch',
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'provider': 'stitch',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_capabilities(self) -> List[str]:
        """Get Stitch capabilities"""
        return ['payment_initiation', 'payouts', 'limited_account_access']


class OkraProvider(BankingProvider):
    """Okra banking provider for Nigeria"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key')
        self.base_url = config.get('base_url', 'https://api.okra.ng/v2')

        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json'
        }

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create Okra widget token"""
        url = f"{self.base_url}/widget/url"

        payload = {
            'success_url': 'https://yourapp.com/banking/callback/okra/success',
            'fail_url': 'https://yourapp.com/banking/callback/okra/failed',
            'callback_url': 'https://yourapp.com/webhooks/okra',
            'customer': {
                'id': user_id,
                'name': f"User {user_id}",
                'email': f"user{user_id}@example.com"  # Should get from user object
            },
            'products': ['auth', 'identity', 'balance', 'transactions'],
            'env': 'production-sandbox',  # or 'production'
            'color': '#4F46E5',
            'limit': 1  # Number of accounts to link
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if data.get('status') == 'success':
                return {
                    'provider': 'okra',
                    'method': 'connect_widget',
                    'widget_url': data['data']['url'],
                    'widget_id': data['data']['id'],
                    'country': 'NG',
                    'instructions': 'Redirect user to the widget URL'
                }
            else:
                return {
                    'provider': 'okra',
                    'error': data.get('message', 'Failed to create widget'),
                    'country': 'NG'
                }

        except Exception as e:
            return {
                'provider': 'okra',
                'error': str(e),
                'country': 'NG'
            }

    def get_widget_status(self, widget_id: str) -> Dict[str, Any]:
        """Get Okra widget status"""
        url = f"{self.base_url}/widget/url/status?id={widget_id}"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            return {
                'widget_id': widget_id,
                'status': data.get('status'),
                'data': data.get('data', {}),
                'provider': 'okra'
            }

        except Exception as e:
            return {
                'widget_id': widget_id,
                'error': str(e),
                'provider': 'okra'
            }

    def get_accounts(self, record_id: str = None, customer_id: str = None) -> List[Dict[str, Any]]:
        """Get Okra accounts"""
        url = f"{self.base_url}/accounts/get"

        payload = {}
        if record_id:
            payload['record'] = record_id
        if customer_id:
            payload['customer'] = customer_id

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            accounts = []
            if data.get('status') == 'success':
                for account in data.get('data', {}).get('accounts', []):
                    accounts.append({
                        'account_id': account.get('_id'),
                        'record_id': account.get('record'),
                        'bank': account.get('bank'),
                        'account_name': account.get('account_name'),
                        'account_number': account.get('account_number'),
                        'currency': account.get('currency', 'NGN'),
                        'balance': account.get('balance'),
                        'provider': 'okra'
                    })

            return accounts

        except Exception as e:
            print(f"Error getting Okra accounts: {e}")
            return []

    def get_transactions(self, record_id: str = None,
                         customer_id: str = None,
                         start_date: str = None,
                         end_date: str = None) -> List[Dict[str, Any]]:
        """Get Okra transactions"""
        url = f"{self.base_url}/transactions/get"

        payload = {}
        if record_id:
            payload['record'] = record_id
        if customer_id:
            payload['customer'] = customer_id

        # Okra supports date filtering
        if start_date and end_date:
            payload['from'] = start_date
            payload['to'] = end_date

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            transactions = []
            if data.get('status') == 'success':
                for txn in data.get('data', {}).get('transactions', []):
                    transactions.append({
                        'transaction_id': txn.get('_id'),
                        'amount': txn.get('amount'),
                        'currency': txn.get('currency', 'NGN'),
                        'description': txn.get('description'),
                        'type': txn.get('type'),
                        'category': txn.get('category'),
                        'balance': txn.get('balance'),
                        'date': txn.get('date'),
                        'record_id': record_id,
                        'provider': 'okra'
                    })

            return transactions

        except Exception as e:
            print(f"Error getting Okra transactions: {e}")
            return []

    def get_balance(self, record_id: str = None, customer_id: str = None) -> List[Dict[str, Any]]:
        """Get Okra balance"""
        url = f"{self.base_url}/balance/get"

        payload = {}
        if record_id:
            payload['record'] = record_id
        if customer_id:
            payload['customer'] = customer_id

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            balances = []
            if data.get('status') == 'success':
                for balance in data.get('data', {}).get('balances', []):
                    balances.append({
                        'record_id': record_id,
                        'balance': balance.get('balance'),
                        'currency': balance.get('currency', 'NGN'),
                        'account_number': balance.get('account_number'),
                        'provider': 'okra'
                    })

            return balances

        except Exception as e:
            print(f"Error getting Okra balance: {e}")
            return []

    def get_income(self, customer_id: str) -> Dict[str, Any]:
        """Get income insights (Okra's feature)"""
        url = f"{self.base_url}/income/get"

        payload = {
            'customer': customer_id
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if data.get('status') == 'success':
                return {
                    'customer_id': customer_id,
                    'income_data': data.get('data', {}),
                    'provider': 'okra'
                }
            else:
                return {}

        except Exception as e:
            print(f"Error getting Okra income: {e}")
            return {}

    def get_identity(self, record_id: str = None, customer_id: str = None) -> Dict[str, Any]:
        """Get identity information"""
        url = f"{self.base_url}/identity/get"

        payload = {}
        if record_id:
            payload['record'] = record_id
        if customer_id:
            payload['customer'] = customer_id

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()

            if data.get('status') == 'success':
                identity = data.get('data', {}).get('identity', {})
                return {
                    'record_id': record_id,
                    'identity': {
                        'name': identity.get('full_name'),
                        'email': identity.get('email'),
                        'phone': identity.get('phone'),
                        'gender': identity.get('gender'),
                        'address': identity.get('address'),
                        'bvn': identity.get('bvn')
                    },
                    'provider': 'okra'
                }
            else:
                return {}

        except Exception as e:
            print(f"Error getting Okra identity: {e}")
            return {}

    def get_institution(self, bank_id: str) -> Dict[str, Any]:
        """Get bank information"""
        # Okra might have a banks endpoint
        return {
            'name': 'Nigerian Bank',
            'provider': 'okra',
            'country': 'NG'
        }

    def health_check(self) -> Dict[str, Any]:
        """Check Okra API health"""
        try:
            # Try a simple endpoint
            response = requests.get(f"{self.base_url}/banks", headers=self.headers)

            if response.status_code == 200:
                return {
                    'provider': 'okra',
                    'status': 'healthy',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'provider': 'okra',
                    'status': 'unhealthy',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.utcnow().isoformat()
                }

        except Exception as e:
            return {
                'provider': 'okra',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def get_capabilities(self) -> List[str]:
        """Get Okra capabilities"""
        return ['transactions', 'balance', 'identity', 'income_insights', 'account_linking']



class TrueLayerProvider(BankingProvider):
    """TrueLayer banking provider for Europe"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')

        # TrueLayer environments
        sandbox = config.get('sandbox', True)
        self.auth_base = "https://auth.truelayer-sandbox.com" if sandbox else "https://auth.truelayer.com"
        self.api_base = "https://api.truelayer-sandbox.com" if sandbox else "https://api.truelayer.com"

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create TrueLayer OAuth authorization URL"""
        # Determine providers based on country
        providers = self._get_providers_for_country(country_code)

        scopes = [
            "info",
            "accounts",
            "balance",
            "transactions",
            "cards",
            "offline_access"
        ]

        auth_url = f"{self.auth_base}/?response_type=code" \
                   f"&client_id={self.client_id}" \
                   f"&redirect_uri={self.redirect_uri}" \
                   f"&scope={' '.join(scopes)}" \
                   f"&providers={','.join(providers)}" \
                   f"&state={user_id}"

        return {
            'provider': 'truelayer',
            'auth_url': auth_url,
            'method': 'oauth_redirect',
            'country': country_code,
            'providers': providers
        }

    def exchange_token(self, authorization_code: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        token_url = f"{self.auth_base}/connect/token"

        auth_string = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()

        headers = {
            'Authorization': f'Basic {encoded_auth}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': authorization_code
        }

        try:
            response = requests.post(token_url, headers=headers, data=data)
            data = response.json()

            return {
                'access_token': data['access_token'],
                'refresh_token': data.get('refresh_token'),
                'expires_in': data.get('expires_in'),
                'provider': 'truelayer'
            }

        except Exception as e:
            return {
                'error': str(e),
                'provider': 'truelayer'
            }

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get TrueLayer accounts"""
        url = f"{self.api_base}/data/v1/accounts"

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            data = response.json()

            accounts = []
            for account in data.get('results', []):
                accounts.append({
                    'account_id': account['account_id'],
                    'account_type': account['account_type'],
                    'display_name': account['display_name'],
                    'currency': account['currency'],
                    'account_number': account.get('account_number', {}),
                    'provider': account['provider']
                })

            return accounts

        except Exception as e:
            print(f"Error getting TrueLayer accounts: {e}")
            return []

    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get TrueLayer transactions"""
        transactions = []

        # If no specific accounts, get all
        if not account_ids:
            accounts = self.get_accounts(access_token)
            account_ids = [acc['account_id'] for acc in accounts]

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        for account_id in account_ids:
            url = f"{self.api_base}/data/v1/accounts/{account_id}/transactions"

            params = {
                'from': start_date,
                'to': end_date
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                data = response.json()

                for txn in data.get('results', []):
                    transactions.append({
                        'transaction_id': txn['transaction_id'],
                        'timestamp': txn['timestamp'],
                        'description': txn['description'],
                        'amount': txn['amount'],
                        'currency': txn['currency'],
                        'transaction_type': txn['transaction_type'],
                        'transaction_category': txn.get('transaction_category'),
                        'merchant_name': txn.get('merchant_name'),
                        'account_id': account_id,
                        'provider': 'truelayer'
                    })

            except Exception as e:
                print(f"Error getting transactions for account {account_id}: {e}")
                continue

        return transactions

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get TrueLayer balances"""
        balances = []

        if not account_ids:
            accounts = self.get_accounts(access_token)
            account_ids = [acc['account_id'] for acc in accounts]

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        for account_id in account_ids:
            url = f"{self.api_base}/data/v1/accounts/{account_id}/balance"

            try:
                response = requests.get(url, headers=headers)
                data = response.json()

                for balance in data.get('results', []):
                    balances.append({
                        'account_id': account_id,
                        'current': balance['current'],
                        'available': balance.get('available'),
                        'currency': balance['currency'],
                        'update_timestamp': balance['update_timestamp'],
                        'provider': 'truelayer'
                    })

            except Exception as e:
                print(f"Error getting balance for account {account_id}: {e}")
                continue

        return balances

    def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """TrueLayer doesn't have institution lookup like Plaid"""
        return {
            'name': 'European Bank',
            'provider': 'truelayer'
        }

    def _get_providers_for_country(self, country_code: str) -> List[str]:
        """Get TrueLayer providers for a country"""
        providers_map = {
            'GB': ['uk-ob-all', 'uk-oauth-all'],
            'IE': ['ie-oauth-all'],
            'ES': ['es-oauth-all'],
            'FR': ['fr-oauth-all'],
            'DE': ['de-oauth-all'],
            'IT': ['it-oauth-all'],
            'NL': ['nl-oauth-all'],
        }

        return providers_map.get(country_code.upper(), ['uk-ob-all'])

    def health_check(self) -> Dict[str, Any]:
        """Check TrueLayer API health"""
        return {
            'provider': 'truelayer',
            'status': 'unknown',  # Would need to implement actual check
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_capabilities(self) -> List[str]:
        """Get TrueLayer capabilities"""
        return ['transactions', 'balances', 'accounts', 'cards', 'direct_debits']




class ProviderRegistry:
    """Registry for all banking providers"""

    # Provider priority by country (first is default)
    COUNTRY_PROVIDERS = {
        # North America
        'US': ['plaid'],
        'CA': ['plaid'],

        # Europe
        'GB': ['plaid', 'truelayer'],
        'IE': ['plaid', 'truelayer'],
        'ES': ['plaid', 'truelayer'],
        'FR': ['plaid', 'truelayer'],
        'DE': ['plaid', 'truelayer'],
        'NL': ['plaid', 'truelayer'],

        # Africa
        'NG': ['flutterwave', 'paystack', 'mono'],  # Nigeria
        'GH': ['flutterwave', 'paystack'],  # Ghana
        'KE': ['flutterwave'],  # Kenya
        'ZA': ['flutterwave'],  # South Africa
        'RW': ['flutterwave'],  # Rwanda
        'UG': ['flutterwave'],  # Uganda
        'TZ': ['flutterwave'],  # Tanzania
        'EG': ['flutterwave'],  # Egypt

        # Add more as needed
    }

    # Provider classes mapping
    PROVIDER_CLASSES = {
        'plaid': PlaidProvider,
        'flutterwave': FlutterwaveProvider,
        'paystack': PaystackProvider,
        'mono': MonoProvider,
        'truelayer': TrueLayerProvider,
        'stitch':StitchProvider,
        'okra': OkraProvider,
        
    }

    @classmethod
    def get_providers_for_country(cls, country_code: str) -> List[str]:
        """Get available providers for a country"""
        return cls.COUNTRY_PROVIDERS.get(country_code.upper(), [])

    @classmethod
    def get_default_provider_for_country(cls, country_code: str) -> Optional[str]:
        """Get default (preferred) provider for a country"""
        providers = cls.get_providers_for_country(country_code)
        return providers[0] if providers else None

    @classmethod
    def create_provider(cls, provider_name: str, config: Dict) -> BankingProvider:
        """Create a provider instance"""
        provider_class = cls.PROVIDER_CLASSES.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        return provider_class(config)

    @classmethod
    def get_supported_countries(cls) -> Dict[str, List[str]]:
        """Get all countries with their supported providers"""
        return cls.COUNTRY_PROVIDERS

    @classmethod
    def is_provider_supported(cls, provider_name: str, country_code: str) -> bool:
        """Check if provider is supported for a country"""
        providers = cls.get_providers_for_country(country_code)
        return provider_name.lower() in providers


def get_user_task_session():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user).first()
    if user:
        engine = create_engine(f"sqlite:///{user.db_name}")
        Session = sessionmaker(bind=engine)
        return Session()
    return None

def generate_token(email):
    return serializer.dumps(email, salt="email-confirm-salt")

def confirm_token(token, expiration=3600):
    try:
        email = serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
    except Exception:
        return None
    return email

def send_email(to, subject, template):
    msg = Message(subject, recipients=[to], html=template, sender=app.config['MAIL_USERNAME'])
    mail.send(msg)

# def log_activity(user, action):
#     log = Activity(
#         user_id=user.id if user else None,
#         action=action,
#         ip_address=request.remote_addr,
#         user_agent=request.headers.get('User-Agent')
#     )
#     db.session.add(log)
#     db.session.commit()
def log_activity(user, action):

    """
    Accepts:
      - user: User instance OR username/email string OR integer user id OR None
      - action: string
    This function resolves the user id when needed, handles errors, and
    never lets exceptions silently prevent logging.
    """
    try:
        # Resolve user id
        user_id = None
        if user is None:
            user_id = None
        elif isinstance(user, int):
            user_id = user
        elif isinstance(user, str):
            # try username then email
            u = User.query.filter_by(username=user).first()
            if not u:
                u = User.query.filter_by(email=user).first()
            user_id = u.id if u else None
        else:
            # assume it's a User instance
            user_id = getattr(user, "id", None)

        log = Activity(
            user_id=user_id,
            action=action,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None
        )
        db.session.add(log)
        db.session.commit()
        # optional debug
        print(f"✅ Activity logged: user_id={user_id}, action={action}")
    except Exception as e:
        # rollback to keep session clean & print error for debugging
        db.session.rollback()
        print(f"❌ Failed to log activity: {e}")

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_identity = get_jwt_identity()
        user = User.query.filter_by(username=current_identity).first()

        if not user or not user.is_admin:
            return jsonify({"message": "Access denied: Admins only"}), 403

        return fn(*args, **kwargs)
    return wrapper

#ML
def process_new_transaction(user, description, amount, date=None):
    date = date or datetime.utcnow()
    category, confidence = categorize_transaction(description)

    transaction = Transaction(
        user_id=user.id,
        description=description,
        amount=amount,
        date=date,
        category=category,
        ml_confidence=confidence
    )
    db.session.add(transaction)
    db.session.commit()

    user_transactions = Transaction.query.filter_by(user_id=user.id).all()
    insights = analyze_spending(user_transactions)

    if not description:
        insights.insert(0, "⚠️ Transaction missing description!")

    return {
        "transaction_category": category,
        "transaction_confidence": confidence,
        "insights": insights
    }
