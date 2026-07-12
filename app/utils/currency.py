"""Backend currency helpers shared by API responses and AI prompts."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


DEFAULT_CURRENCY = "USD"

CURRENCY_SYMBOLS = {
    "USD": "$",
    "NGN": "₦",
    "EUR": "€",
    "GBP": "£",
    "GHS": "₵",
    "KES": "KSh",
    "ZAR": "R",
    "EGP": "E£",
    "XOF": "CFA",
    "XAF": "FCFA",
    "CAD": "$",
    "AUD": "$",
    "BRL": "R$",
    "MXN": "$",
    "JPY": "¥",
    "INR": "₹",
}

ZERO_DECIMAL_CURRENCIES = {"BIF", "CLP", "DJF", "GNF", "JPY", "KMF", "KRW", "PYG", "RWF", "UGX", "VND", "XAF", "XOF", "XPF"}


def normalize_currency(currency: str | None) -> str:
    return (currency or DEFAULT_CURRENCY).upper()


def currency_symbol(currency: str | None) -> str:
    code = normalize_currency(currency)
    return CURRENCY_SYMBOLS.get(code, code)


def currency_decimals(currency: str | None) -> int:
    return 0 if normalize_currency(currency) in ZERO_DECIMAL_CURRENCIES else 2


def format_currency(amount: float | int | Decimal, currency: str | None) -> str:
    code = normalize_currency(currency)
    decimals = currency_decimals(code)
    try:
        value = Decimal(str(amount))
    except InvalidOperation:
        value = Decimal("0")
    return f"{currency_symbol(code)}{value:,.{decimals}f}"
