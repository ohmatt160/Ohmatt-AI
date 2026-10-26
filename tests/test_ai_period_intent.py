from app.services.transaction_context_service import TransactionContextService


def test_broad_finance_questions_use_period_default_not_merchant_search():
    assert TransactionContextService._search_terms("How am I doing?") == []
    assert TransactionContextService._search_terms("Tell me about my expenses") == []
    assert TransactionContextService._search_terms("What did I pay HiddenMerchant?") == ["hiddenmerchant"]
