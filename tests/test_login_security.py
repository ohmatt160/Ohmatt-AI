from types import SimpleNamespace

import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from app.routes.auth import issue_2fa_code, send_login_challenge, verify_2fa_code
from app.schemas.user import ProfileUpdate
from app.services.user_service import UserService
from app.config import settings


def test_login_code_is_hashed_and_single_use():
    user = SimpleNamespace(preferences={})
    code = issue_2fa_code(user)

    assert code.isdigit() and len(code) == 6
    assert "two_factor_code" not in user.preferences
    assert user.preferences["two_factor_code_hash"] != code
    assert verify_2fa_code(user, code)
    assert not verify_2fa_code(user, code)


def test_profile_update_cannot_bypass_two_factor_flow():
    with pytest.raises(ValidationError):
        ProfileUpdate(two_factor_enabled=False)


def test_login_challenge_sends_directly_and_persists_only_hash(monkeypatch):
    sent = []
    monkeypatch.setattr("app.routes.auth.send_plain_email", lambda email, subject, body: sent.append((email, subject, body)) or True)
    user = SimpleNamespace(id=7, email="admin@example.com", preferences={})
    db = SimpleNamespace(commit=lambda: None)

    send_login_challenge(db, user)

    assert sent and sent[0][0] == user.email
    assert user.preferences["two_factor_code_hash"]
    assert "two_factor_code" not in user.preferences
    assert user.preferences["login_challenge_last_sent_at"]


def test_failed_login_email_clears_unusable_code(monkeypatch):
    monkeypatch.setattr("app.routes.auth.send_plain_email", lambda *_args: False)
    user = SimpleNamespace(id=7, email="admin@example.com", preferences={})
    db = SimpleNamespace(commit=lambda: None)

    with pytest.raises(HTTPException) as error:
        send_login_challenge(db, user)

    assert error.value.status_code == 503
    assert "two_factor_code_hash" not in user.preferences
    assert "two_factor_expires_at" not in user.preferences


def test_existing_allowlisted_admin_is_verified_when_authenticating(monkeypatch):
    user = SimpleNamespace(
        email="admin@example.com",
        is_admin=True,
        is_verified=False,
        preferences={},
        check_password=lambda _password: True,
    )

    class Query:
        def filter(self, *_args):
            return self

        def first(self):
            return user

    class Database:
        commits = 0

        def query(self, *_args):
            return Query()

        def commit(self):
            self.commits += 1

        def refresh(self, _user):
            pass

    db = Database()
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@example.com")
    result = UserService.authenticate_user(db, "admin@example.com", "valid-password")

    assert result is user
    assert user.is_verified is True
    assert db.commits == 1
