from app.providers.mono_provider import MonoProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.responses.pop(0)


def make_provider(responses):
    return MonoProvider({
        "secret_key": "test-secret",
        "public_key": "test-public",
        "default_currency": "NGN",
        "session": FakeSession(responses),
    })


def test_get_accounts_uses_v2_and_preserves_zero_balance():
    provider = make_provider([FakeResponse({
        "meta": {"data_status": "AVAILABLE"},
        "account": {
            "_id": "account-1",
            "name": "Ada User",
            "accountNumber": "0123456789",
            "currency": "NGN",
            "balance": 0,
            "type": "savings",
            "institution": {"name": "Test Bank", "bankCode": "001"},
        },
    })])

    accounts = provider.get_accounts("account-1")

    assert accounts[0]["balances"]["current"] == 0
    assert provider.session.calls[0][1].endswith("/v2/accounts/account-1")
    assert provider.session.calls[0][2]["headers"]["x-real-time"] == "true"


def test_get_transactions_fetches_every_page_and_preserves_direction():
    provider = make_provider([
        FakeResponse({
            "data": [{"_id": "tx-1", "type": "debit", "amount": 2500, "date": "2026-01-01T10:00:00Z"}],
            "meta": {"total": 2, "page": 1, "next": "page-2"},
        }),
        FakeResponse({
            "data": [{"_id": "tx-2", "type": "credit", "amount": 5000, "date": "2026-01-02T10:00:00Z"}],
            "meta": {"total": 2, "page": 2, "next": None},
        }),
    ])

    transactions = provider.get_transactions("account-1", "1970-01-01", "2026-01-03")

    assert [item["transaction_id"] for item in transactions] == ["tx-1", "tx-2"]
    assert [item["amount"] for item in transactions] == [25, -50]
    assert provider.session.calls[1][2]["params"]["page"] == 2
