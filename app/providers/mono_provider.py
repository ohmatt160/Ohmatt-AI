# app/providers/mono_provider.py
from typing import Dict, Any, List, Optional
import logging
import requests
from datetime import datetime

from app.providers.base_provider import BankingProvider

logger = logging.getLogger(__name__)


class MonoProvider(BankingProvider):
    """Mono banking provider for markets supported by Mono"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.secret_key = config.get('secret_key')
        self.public_key = config.get('public_key')
        self.base_url = config.get('base_url', 'https://api.withmono.com')
        self.default_currency = (config.get('default_currency') or 'USD').upper()
        self.session = config.get('session') or requests.Session()
        self.timeout = config.get('timeout', (5, 30))

        self.headers = {
            'Accept': 'application/json',
            'mono-sec-key': self.secret_key,
            'Content-Type': 'application/json'
        }

    def _request_json(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        response = self.session.request(
            method,
            f"{self.base_url.rstrip('/')}/{path.lstrip('/')}",
            headers=kwargs.pop('headers', self.headers),
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code >= 400:
            logger.warning("Mono request failed endpoint=%s status=%s", path, response.status_code)
            raise RuntimeError(f"Mono API request failed ({response.status_code})")
        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("Mono returned an invalid response") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("Mono returned an invalid response")
        return payload

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
        try:
            result = self._request_json('POST', '/v2/accounts/auth', json={'code': authorization_code})
            account_id = result.get('id') or (result.get('data') or {}).get('id')
            if not account_id:
                raise RuntimeError("Mono did not return an account ID")
            return {'access_token': account_id, 'provider': 'mono'}
        except RuntimeError:
            logger.exception("Mono token exchange failed")
            return {
                'success': False,
                'error': 'Bank authorization could not be completed',
                'provider': 'mono'
            }

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get user's bank accounts from Mono"""
        headers = {**self.headers, 'x-real-time': 'true'}
        data = self._request_json('GET', f'/v2/accounts/{access_token}', headers=headers)
        meta = data.get('meta') or {}
        if meta.get('data_status') in {'FAILED', 'UNAVAILABLE'}:
            raise RuntimeError("Bank account data is unavailable")
        account = data.get('account') or (data.get('data') or {}).get('account')
        if not account:
            raise RuntimeError("Bank account data is still processing")
        raw_balance = account.get('balance')
        balance = float(raw_balance) / 100 if raw_balance is not None else None
        currency = account.get('currency') or self.default_currency
        return [{
            'account_id': account.get('_id') or access_token,
            'name': account.get('name') or 'Bank Account',
            'account_number': account.get('accountNumber', ''),
            'type': account.get('type', 'savings'),
            'currency': currency,
            'balances': {
                'available': balance,
                'current': balance,
                'limit': None,
                'currency': currency,
            },
            'institution': {
                'name': (account.get('institution') or {}).get('name', ''),
                'bank_code': (account.get('institution') or {}).get('bankCode', ''),
                'type': (account.get('institution') or {}).get('type', ''),
            },
        }]

    def get_transactions(self, access_token: str,
                         start_date: str,
                         end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get transactions from Mono"""
        transactions = []
        page = 1
        seen_pages = set()
        seen_page_signatures = set()
        headers = {**self.headers, 'x-real-time': 'true'}
        while page not in seen_pages:
            seen_pages.add(page)
            payload = self._request_json(
                'GET',
                f'/v2/accounts/{access_token}/transactions',
                headers=headers,
                params={'start': start_date, 'end': end_date, 'limit': 100, 'page': page},
            )
            data = payload.get('data') or []
            records = data.get('transactions', []) if isinstance(data, dict) else data
            if not isinstance(records, list):
                raise RuntimeError("Mono returned invalid transaction data")
            signature = tuple(str(txn.get('_id') or txn.get('id')) for txn in records)
            if signature and signature in seen_page_signatures:
                raise RuntimeError("Mono returned repeated transaction pages")
            seen_page_signatures.add(signature)
            for txn in records:
                raw_amount = float(txn.get('amount') or 0) / 100
                transaction_type = str(txn.get('type') or '').lower()
                amount = -abs(raw_amount) if transaction_type == 'credit' else abs(raw_amount)
                transactions.append({
                    'transaction_id': txn.get('_id') or txn.get('id'),
                    'account_id': txn.get('account') or access_token,
                    'amount': amount,
                    'date': txn.get('date'),
                    'description': txn.get('narration', ''),
                    'merchant_name': txn.get('beneficiary', ''),
                    'category': txn.get('category', ''),
                    'type': transaction_type,
                    'currency': txn.get('currency') or self.default_currency,
                    'pending': False,
                    'provider': 'mono',
                })

            paging = payload.get('meta') or payload.get('paging') or (
                data.get('paging', {}) if isinstance(data, dict) else {}
            )
            total = int(paging.get('total') or 0)
            has_next = bool(paging.get('next')) or (total > page * 100)
            if not has_next:
                break
            if not records:
                raise RuntimeError("Mono pagination ended before all transactions were returned")
            page += 1
        return transactions

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get account balances"""
        return [
            {
                'account_id': account['account_id'],
                'currency': account['balances']['currency'],
                'available': account['balances']['available'],
                'ledger': account['balances']['current'],
            }
            for account in self.get_accounts(access_token)
        ]

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
        """Verify bank account details where the provider supports it"""
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
                    'currency': self.default_currency,
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
