from app.routes.auth import classify_sendgrid_failure


def test_sendgrid_401_classifies_free_trial_credit_limit():
    assert classify_sendgrid_failure(401, '{"errors":[{"message":"Maximum credits exceeded"}]}') == "free_trial_credit_limit"


def test_sendgrid_401_does_not_claim_key_invalid_without_provider_detail():
    assert classify_sendgrid_failure(401, "authorization grant is invalid") == "invalid_api_key_or_permissions"
