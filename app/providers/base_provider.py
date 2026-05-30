from datetime import datetime
from typing import Dict, Any, List, Optional
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