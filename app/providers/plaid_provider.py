from typing import Dict, Any, List, Optional
from datetime import datetime
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from app.providers.base_provider import BankingProvider

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

            request_data = {
                "user": {"client_user_id": str(user_id)},
                "client_name": "Ohmatt Finance AI",
                "products": products,
                "country_codes": [plaid_country],
                "language": "en",
            }

            redirect_uri = self.config.get('redirect_uri')
            webhook_url = self.config.get('webhook_url')
            if redirect_uri:
                request_data["redirect_uri"] = redirect_uri
            if webhook_url:
                request_data["webhook"] = webhook_url

            request = LinkTokenCreateRequest(**request_data)

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
