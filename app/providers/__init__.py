"""Banking provider registry keyed by supported country/region."""

from __future__ import annotations


DEFAULT_PROVIDER = "stripe"

PROVIDER_REGIONS = {
    "AE": ["stripe"],
    "AO": ["flutterwave", "stripe"],
    "BR": ["stripe"],
    "CA": ["plaid", "stripe"],
    "EG": ["fawry", "stripe"],
    "EU": ["truelayer", "stripe"],
    "FR": ["truelayer", "stripe"],
    "GB": ["plaid", "truelayer", "stripe"],
    "GH": ["flutterwave", "paystack"],
    "KE": ["flutterwave", "mpesa"],
    "MA": ["stripe"],
    "MZ": ["flutterwave", "stripe"],
    "NG": ["flutterwave", "paystack", "mono"],
    "PT": ["truelayer", "stripe"],
    "RW": ["flutterwave", "stripe"],
    "SN": ["flutterwave", "stripe"],
    "TZ": ["flutterwave", "mpesa"],
    "UG": ["flutterwave", "mpesa"],
    "US": ["plaid", "stripe"],
    "ZA": ["stitch", "stripe"],
}

PROVIDER_METADATA = {
    "fawry": {"name": "Fawry", "features": ["payments", "verification"]},
    "flutterwave": {"name": "Flutterwave", "features": ["transactions", "verification"]},
    "mono": {"name": "Mono", "features": ["account_linking", "transactions", "identity"]},
    "mpesa": {"name": "M-Pesa", "features": ["transactions", "mobile_money"]},
    "paystack": {"name": "Paystack", "features": ["transactions", "verification"]},
    "plaid": {"name": "Plaid", "features": ["transactions", "balances", "auth"]},
    "stitch": {"name": "Stitch", "features": ["transactions", "balances"]},
    "stripe": {"name": "Stripe", "features": ["payments", "balances"]},
    "truelayer": {"name": "TrueLayer", "features": ["transactions", "balances", "auth"]},
}


def get_providers_for_country(country_code: str | None) -> list[str]:
    code = (country_code or "").upper()
    return PROVIDER_REGIONS.get(code, [DEFAULT_PROVIDER])


def provider_metadata(provider_code: str) -> dict:
    code = provider_code.lower()
    metadata = PROVIDER_METADATA.get(code, {})
    return {
        "code": code,
        "name": metadata.get("name") or code.replace("_", " ").title(),
        "features": metadata.get("features") or ["transactions", "balances"],
    }
