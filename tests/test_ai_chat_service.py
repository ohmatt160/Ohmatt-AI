from types import SimpleNamespace

import httpx
from openai import AuthenticationError

from app.config import settings
from app.services.ai_chat_service import AIChatService


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeClient:
    def __init__(self, content):
        self.completions = FakeCompletions(content)
        self.chat = SimpleNamespace(completions=self.completions)


class FailingCompletions:
    def create(self, **kwargs):
        request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        response = httpx.Response(401, request=request, headers={"x-request-id": "req_test"})
        raise AuthenticationError("Invalid API Key", response=response, body={"error": "invalid_api_key"})


class FailingClient:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FailingCompletions())


def test_chat_uses_groq_model_and_verified_context(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_key_that_is_not_a_real_secret")
    monkeypatch.setattr(settings, "GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")

    fake_client = FakeClient("Your spending looks steady.")
    service = AIChatService()
    monkeypatch.setattr(service, "_client", lambda: fake_client)
    monkeypatch.setattr(
        "app.services.ai_chat_service.transaction_context_service.build",
        lambda *args: "Verified ledger coverage: all 2 transactions.",
    )
    user = SimpleNamespace(id=42, username="matt", preferences={"currency": "NGN"})

    response = service.respond(db=object(), user=user, message="How am I doing?")

    assert response == "Your spending looks steady."
    request = fake_client.completions.calls[0]
    assert request["model"] == "llama-3.3-70b-versatile"
    assert "Verified ledger coverage: all 2 transactions." in request["messages"][1]["content"]
    assert request["temperature"] == 0.25


def test_chat_reports_missing_groq_key_without_guessing(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(
        "app.services.ai_chat_service.transaction_context_service.build",
        lambda *args: "Verified ledger coverage: 0 transactions.",
    )
    user = SimpleNamespace(id=42, username="matt", preferences={"currency": "NGN"})

    response = AIChatService().respond(db=object(), user=user, message="Hello")

    assert response == "AI chat is being configured right now. Please try again shortly."


def test_chat_rejects_empty_provider_response(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_key_that_is_not_a_real_secret")
    service = AIChatService()
    monkeypatch.setattr(service, "_client", lambda: FakeClient("  "))
    monkeypatch.setattr(
        "app.services.ai_chat_service.transaction_context_service.build",
        lambda *args: "Verified ledger coverage: 0 transactions.",
    )
    user = SimpleNamespace(id=42, username="matt", preferences={"currency": "NGN"})

    response = service.respond(db=object(), user=user, message="Hello")

    assert response == "AI chat is being configured right now. Please try again shortly."


def test_chat_reports_provider_credential_errors_without_exposing_details(monkeypatch):
    monkeypatch.setattr(settings, "GROQ_API_KEY", "gsk_test_key_that_is_not_a_real_secret")
    service = AIChatService()
    monkeypatch.setattr(service, "_client", FailingClient)
    monkeypatch.setattr(
        "app.services.ai_chat_service.transaction_context_service.build",
        lambda *args: "Verified ledger coverage: 0 transactions.",
    )
    user = SimpleNamespace(id=42, username="matt", preferences={"currency": "NGN"})

    response = service.respond(db=object(), user=user, message="Hello")

    assert response == (
        "AI chat is temporarily unavailable while its secure provider connection is being renewed. "
        "Please try again shortly."
    )
