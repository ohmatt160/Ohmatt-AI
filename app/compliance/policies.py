"""Data protection policy registry.

These policies are intentionally descriptive. Enforcement should stay in route
handlers and services that perform deletion, export, retention, and consent
workflows.
"""

from __future__ import annotations


COMPLIANCE_POLICIES = {
    "GDPR": {
        "regions": ["EU", "GB"],
        "retention_days": 365,
        "rights": ["access", "deletion", "export", "rectification", "restriction"],
        "requires_consent": True,
    },
    "CCPA": {
        "regions": ["US-CA"],
        "retention_days": 365,
        "rights": ["access", "deletion", "opt_out_sale", "non_discrimination"],
        "requires_consent": False,
    },
    "NDPR": {
        "regions": ["NG"],
        "retention_days": 365,
        "rights": ["access", "deletion", "export", "correction"],
        "requires_consent": True,
    },
    "DEFAULT": {
        "regions": ["*"],
        "retention_days": 365,
        "rights": ["access", "deletion", "export"],
        "requires_consent": False,
    },
}


def get_compliance_policy(country_code: str | None, region_code: str | None = None) -> dict:
    country = (country_code or "").upper()
    region = (region_code or "").upper()
    lookup = f"{country}-{region}" if region else country

    for policy in COMPLIANCE_POLICIES.values():
        if lookup in policy["regions"] or country in policy["regions"]:
            return policy
    if country in {"AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO", "SE", "SI", "SK"}:
        return COMPLIANCE_POLICIES["GDPR"]
    return COMPLIANCE_POLICIES["DEFAULT"]
