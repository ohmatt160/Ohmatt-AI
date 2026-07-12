from unittest.mock import Mock

import pytest

from app.providers.flutterwave_provider import FlutterwaveProvider


def make_provider() -> FlutterwaveProvider:
    return FlutterwaveProvider({
        "enabled": True,
        "secret_key": "test-secret",
        "base_url": "https://api.flutterwave.com/v3",
    })


def test_provider_fails_closed_without_enabled_credentials():
    provider = FlutterwaveProvider({"enabled": False, "secret_key": ""})

    with pytest.raises(RuntimeError, match="not configured"):
        provider.create_link_token("1", "NG")


def test_verify_account_uses_server_credentials_and_timeout():
    provider = make_provider()
    response = Mock(status_code=200)
    response.json.return_value = {
        "status": "success",
        "data": {"account_number": "0123456789", "account_name": "Test User"},
    }
    provider.session.post = Mock(return_value=response)

    result = provider.verify_bank_account("0123456789", "044", "NG")

    assert result["success"] is True
    assert result["account_name"] == "Test User"
    _, kwargs = provider.session.post.call_args
    assert kwargs["json"] == {"account_number": "0123456789", "account_bank": "044"}
    assert kwargs["timeout"] == (3.05, 12)
    assert "X-Trace-Id" in kwargs["headers"]


def test_bank_directory_is_normalized_and_cached():
    provider = make_provider()
    provider._bank_cache.clear()
    response = Mock(status_code=200)
    response.json.return_value = {
        "data": [
            {"id": 2, "code": "999", "name": "Zulu Bank", "type": "BANK"},
            {"id": 1, "code": "044", "name": "Access Bank", "type": "BANK"},
            {"id": 3, "code": "M01", "name": "Mobile Wallet", "type": "MOBILEMONEY"},
        ]
    }
    provider.session.get = Mock(return_value=response)

    first = provider.list_banks("ng")
    second = provider.list_banks("NG")

    assert [bank["code"] for bank in first] == ["044", "999"]
    assert second == first
    provider.session.get.assert_called_once()
