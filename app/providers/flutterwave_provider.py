import logging
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.providers.base_provider import BankingProvider


logger = logging.getLogger(__name__)


class FlutterwaveProvider(BankingProvider):
    """Server-side Flutterwave v3 client for verified bank accounts."""

    _bank_cache: Dict[str, tuple[float, List[Dict[str, Any]]]] = {}
    _cache_lock = threading.Lock()
    _bank_cache_seconds = 3600

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.enabled = bool(config.get("enabled", False))
        self.secret_key = (config.get("secret_key") or "").strip()
        self.base_url = config.get("base_url", "https://api.flutterwave.com/v3").rstrip("/")
        self.timeout = (3.05, 12)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.secret_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        # Retry reads only. Retrying account resolution POSTs could duplicate billable work.
        retries = Retry(
            total=2,
            connect=2,
            read=2,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=50))

    def _ensure_configured(self) -> None:
        if not self.enabled or not self.secret_key:
            raise RuntimeError("Flutterwave is not configured")

    @staticmethod
    def _provider_error(response: requests.Response, fallback: str) -> str:
        if response.status_code == 401:
            return "Bank verification is temporarily unavailable"
        if response.status_code == 429:
            return "Too many verification attempts. Please try again shortly"
        try:
            payload = response.json()
            message = payload.get("message") or payload.get("error", {}).get("message")
            if isinstance(message, str) and message:
                return message[:200]
        except (ValueError, AttributeError):
            pass
        return fallback

    def create_link_token(self, user_id: str, country_code: str) -> Dict[str, Any]:
        self._ensure_configured()
        return {
            "provider": "flutterwave",
            "country": country_code.upper(),
            "auth_type": "account_verification",
            "reference": f"bank-link-{user_id}-{uuid.uuid4().hex}",
            "instructions": "Select a bank and verify the account holder name.",
        }

    def exchange_token(self, authorization_code: str, metadata: Dict) -> Dict[str, Any]:
        return {"success": False, "error": "Flutterwave uses account verification, not OAuth linking"}

    def list_banks(self, country: str) -> List[Dict[str, Any]]:
        self._ensure_configured()
        country = country.upper()
        now = time.monotonic()
        with self._cache_lock:
            cached = self._bank_cache.get(country)
            if cached and cached[0] > now:
                return cached[1]

        response = self.session.get(
            f"{self.base_url}/banks/{country}",
            params={"include_provider_type": "1"},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            logger.warning("Flutterwave bank list failed status=%s country=%s", response.status_code, country)
            raise RuntimeError(self._provider_error(response, "Could not load banks"))

        payload = response.json()
        banks = [
            {"id": item.get("id"), "code": str(item.get("code", "")), "name": item.get("name", "")}
            for item in payload.get("data", [])
            if item.get("code") and item.get("name") and item.get("type", "BANK") != "MOBILEMONEY"
        ]
        banks.sort(key=lambda item: item["name"].casefold())
        with self._cache_lock:
            self._bank_cache[country] = (now + self._bank_cache_seconds, banks)
        return banks

    def verify_bank_account(self, account_number: str, bank_code: str, country: str = "") -> Dict[str, Any]:
        self._ensure_configured()
        trace_id = str(uuid.uuid4())
        try:
            response = self.session.post(
                f"{self.base_url}/accounts/resolve",
                json={"account_number": account_number, "account_bank": bank_code},
                headers={"X-Trace-Id": trace_id},
                timeout=self.timeout,
            )
        except requests.Timeout:
            return {"success": False, "error": "Bank verification timed out. Please try again"}
        except requests.RequestException:
            logger.exception("Flutterwave account resolution transport failure trace_id=%s", trace_id)
            return {"success": False, "error": "Bank verification is temporarily unavailable"}

        try:
            result = response.json()
        except ValueError:
            result = {}
        if response.status_code == 200 and result.get("status") == "success":
            data = result.get("data") or {}
            return {
                "success": True,
                "account_number": str(data.get("account_number") or account_number),
                "account_name": data.get("account_name"),
                "bank_code": bank_code,
                "country": country,
            }

        logger.info("Flutterwave account resolution rejected status=%s trace_id=%s", response.status_code, trace_id)
        return {"success": False, "error": self._provider_error(response, "Account verification failed")}

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        return []

    def get_transactions(self, access_token: str, start_date: str, end_date: str,
                         account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return []

    def get_balances(self, access_token: str,
                     account_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        return []

    def get_institution(self, bank_code: str) -> Dict[str, Any]:
        return {"name": "Bank", "code": bank_code}
