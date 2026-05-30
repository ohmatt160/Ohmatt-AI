from typing import Dict, Any, List, Optional
import requests
import hmac
import hashlib
from datetime import datetime

from app.providers.base_provider import BankingProvider


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

