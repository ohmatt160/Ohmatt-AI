from app.providers import IMPLEMENTED_BANKING_PROVIDERS, get_providers_for_country


def test_bank_connect_never_exposes_unimplemented_payment_providers():
    assert "stripe" not in IMPLEMENTED_BANKING_PROVIDERS
    assert "stripe" not in get_providers_for_country("US")
    assert "stripe" not in get_providers_for_country("AO")


def test_nigeria_returns_only_implemented_bank_connectors():
    assert get_providers_for_country("NG") == ["flutterwave", "paystack", "mono"]


def test_unknown_country_has_no_unsafe_default_provider():
    assert get_providers_for_country(None) == []
    assert get_providers_for_country("XX") == []
