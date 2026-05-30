from typing import Dict, Any, List, Optional
import requests
import uuid

from app.providers.base_provider import BankingProvider





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
                'instructions': 'Verify the account number with the customer bank code.'
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

        try:
            result = response.json()
        except ValueError:
            result = {}

        if response.status_code == 200 and result.get('status') == 'success':
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
                'error': result.get('message', 'Verification failed')
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
