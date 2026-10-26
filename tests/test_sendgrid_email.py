from app.routes import auth
from app.routes.auth import classify_sendgrid_failure


def test_sendgrid_401_classifies_free_trial_credit_limit():
    assert classify_sendgrid_failure(401, '{"errors":[{"message":"Maximum credits exceeded"}]}') == "free_trial_credit_limit"


def test_sendgrid_401_does_not_claim_key_invalid_without_provider_detail():
    assert classify_sendgrid_failure(401, "authorization grant is invalid") == "invalid_api_key_or_permissions"


def test_brevo_email_uses_api_key_and_verified_sender(monkeypatch):
    monkeypatch.setattr(auth.settings, "BREVO_API_KEY", "test-api-key")
    monkeypatch.setattr(auth.settings, "BREVO_FROM_EMAIL", "verified@example.com")
    monkeypatch.setattr(auth.settings, "BREVO_FROM_NAME", "Ohmatt")

    class Response:
        status_code = 201

    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return Response()

    monkeypatch.setattr(auth.requests, "post", fake_post)

    assert auth.send_brevo_email("user@example.com", "Verify", "Your code is 123456")
    assert captured["headers"]["api-key"] == "test-api-key"
    assert captured["json"]["sender"] == {"email": "verified@example.com", "name": "Ohmatt"}
    assert captured["json"]["to"] == [{"email": "user@example.com"}]


def test_brevo_is_selected_when_api_key_is_configured(monkeypatch):
    monkeypatch.setattr(auth.settings, "BREVO_API_KEY", "test-api-key")
    monkeypatch.setattr(auth, "send_brevo_email", lambda *args: True)
    monkeypatch.setattr(auth, "send_sendgrid_email", lambda *args: (_ for _ in ()).throw(AssertionError("SendGrid should not be called")))

    assert auth.send_plain_email("user@example.com", "Verify", "Code")
