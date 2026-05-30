# app/providers/mono_provider.py
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime

from app.providers.base_provider import BankingProvider


class MonoProvider(BankingProvider):
    """Mono banking provider for Nigeria"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key')
        self.base_url = config.get('base_url', 'https://api.withmono.com')

        self.headers = {
            'Accept': 'application/json',
            'mono-sec-key': self.secret_key,
            'Content-Type': 'application/json'
        }

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        """Create Mono connection link"""
        return {
            'provider': 'mono',
            'method': 'direct_connection',
            'country': country_code,
            'public_key': self.public_key,
            'reference': f"ohmatt-{user_id}-{int(datetime.utcnow().timestamp())}",
            'instructions': 'Use Mono Connect widget to link bank account'
        }

    def exchange_token(self, authorization_code: str, metadata: Dict) -> Dict[str, Any]:
        """Exchange public token for access token"""
        url = f"{self.base_url}/v2/accounts/auth"

        data = {
            'code': authorization_code
        }

        try:
            response = requests.post(url, json=data, headers=self.headers)
            result = response.json()

            if response.status_code == 200:
                return {
                    'access_token': result.get('id'),
                    'provider': 'mono'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Token exchange failed'),
                    'provider': 'mono'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'mono'
            }

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's bank accounts from Mono"""
        url = f"{self.base_url}/accounts/{access_token}"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            accounts = []
            if response.status_code == 200 and 'account' in data:
                account = data['account']
                accounts.append({
                    'account_id': account.get('_id'),
                    'name': account.get('account', ''),
                    'account_number': account.get('accountNumber', ''),
                    'type': account.get('type', 'savings'),
                    'currency': account.get('currency', 'NGN'),
                    'balances': {
                        'available': account.get('balance', 0) / 100 if account.get('balance') else 0,
                        'current': account.get('balance', 0) / 100 if account.get('balance') else 0,
                        'limit': 0,
                        'currency': account.get('currency', 'NGN')
                    },
                    'institution': {
                        'name': account.get('institution', {}).get('name', ''),
                        'bank_code': account.get('institution', {}).get('bankCode', ''),
                        'type': account.get('institution', {}).get('type', '')
                    }
                })

            return accounts

        except Exception as e:
            print(f"Error getting Mono accounts: {e}")
            return []

    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get transactions from Mono"""
        url = f"{self.base_url}/accounts/{access_token}/transactions"

        params = {
            'start': start_date,
            'end': end_date,
            'limit': 100
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            data = response.json()

            transactions = []
            if response.status_code == 200 and 'data' in data:
                for txn in data['data']:
                    transactions.append({
                        'transaction_id': txn.get('_id'),
                        'account_id': txn.get('account', ''),
                        'amount': abs(txn.get('amount', 0)) / 100 if txn.get('amount') else 0,
                        'date': txn.get('date'),
                        'description': txn.get('narration', ''),
                        'merchant_name': txn.get('beneficiary', ''),
                        'category': txn.get('category', ''),
                        'type': txn.get('type', ''),
                        'currency': txn.get('currency', 'NGN'),
                        'pending': False,
                        'provider': 'mono'
                    })

            return transactions

        except Exception as e:
            print(f"Error getting Mono transactions: {e}")
            return []

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get account balances"""
        url = f"{self.base_url}/accounts/{access_token}"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            balances = []
            if response.status_code == 200 and 'account' in data:
                account = data['account']
                balances.append({
                    'account_id': account.get('_id'),
                    'currency': account.get('currency', 'NGN'),
                    'available': account.get('balance', 0) / 100 if account.get('balance') else 0,
                    'ledger': account.get('balance', 0) / 100 if account.get('balance') else 0
                })

            return balances

        except Exception as e:
            print(f"Error getting Mono balances: {e}")
            return []

    def get_institution(self, bank_code: str) -> Dict[str, Any]:
        """Get bank/institution information"""
        url = f"{self.base_url}/coverage"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if response.status_code == 200 and 'data' in data:
                for bank in data['data']:
                    if bank.get('bankCode') == bank_code:
                        return {
                            'name': bank.get('bankName', 'Unknown Bank'),
                            'code': bank_code,
                            'provider': 'mono'
                        }

            return {
                'name': 'Unknown Bank',
                'code': bank_code,
                'provider': 'mono'
            }

        except Exception as e:
            print(f"Error getting Mono institution: {e}")
            return {'name': 'Unknown Bank', 'code': bank_code}

    def verify_bank_account(self, account_number: str, bank_code: str) -> Dict[str, Any]:
        """Verify Nigerian bank account details"""
        url = f"{self.base_url}/v1/cac/company/{account_number}"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if response.status_code == 200:
                return {
                    'success': True,
                    'account_number': account_number,
                    'account_name': data.get('data', {}).get('companyName', ''),
                    'bank_code': bank_code,
                    'provider': 'mono'
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Verification failed'),
                    'provider': 'mono'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'provider': 'mono'
            }

    def get_identity(self, access_token: str) -> Dict[str, Any]:
        """Get user identity information"""
        url = f"{self.base_url}/accounts/{access_token}/identity"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if response.status_code == 200 and 'data' in data:
                identity = data['data']
                return {
                    'full_name': identity.get('fullName', ''),
                    'first_name': identity.get('firstName', ''),
                    'last_name': identity.get('lastName', ''),
                    'email': identity.get('email', ''),
                    'phone': identity.get('phone', ''),
                    'bvn': identity.get('bvn', ''),
                    'provider': 'mono'
                }

            return {}

        except Exception as e:
            print(f"Error getting Mono identity: {e}")
            return {}

    def get_income(self, access_token: str) -> Dict[str, Any]:
        """Get income information"""
        url = f"{self.base_url}/accounts/{access_token}/income"

        try:
            response = requests.get(url, headers=self.headers)
            data = response.json()

            if response.status_code == 200 and 'data' in data:
                income = data['data']
                return {
                    'monthly_average': income.get('monthlyAverage', 0) / 100,
                    'total_income': income.get('totalIncome', 0) / 100,
                    'currency': 'NGN',
                    'provider': 'mono'
                }

            return {}

        except Exception as e:
            print(f"Error getting Mono income: {e}")
            return {}

    def health_check(self) -> Dict[str, Any]:
        """Check Mono API health"""
        try:
            response = requests.get(
                f"{self.base_url}/coverage",
                headers=self.headers,
                timeout=5
            )

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
        return ['account_linking', 'transactions', 'identity', 'income', 'cac_verification']
