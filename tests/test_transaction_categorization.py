from app.services.ai_service import AIService


def test_uncategorized_classifier_uses_rules_and_auditable_fallback():
    service = object.__new__(AIService)
    service.vectorizer = None
    service.clf = None
    service.top_n = 3

    assert service.categorize_transaction("Uber trip") == ("Transportation", 0.85)
    assert service.categorize_transaction("Expensive") == ("Other", 0.15)
    assert service.categorize_transaction("") == ("Uncategorized", 0.0)
