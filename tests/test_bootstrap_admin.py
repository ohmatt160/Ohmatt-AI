from types import SimpleNamespace

from app import extensions
from app.config import settings


def test_bootstrap_admin_rename_preserves_password(monkeypatch):
    existing_admin = SimpleNamespace(
        email="ohmatt@admin.com",
        is_admin=True,
        is_verified=True,
        password_hash="existing-password-hash",
    )

    class Query:
        def __init__(self, result):
            self.result = result

        def filter(self, _expression):
            return self

        def first(self):
            return self.result

    class Database:
        results = [None, existing_admin]
        commits = 0

        def query(self, _model):
            return Query(self.results.pop(0))

        def commit(self):
            self.commits += 1

        def flush(self):
            pass

    database = Database()
    monkeypatch.setattr(extensions, "db_session", database)
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_EMAIL", "ohmatt160@gmail.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PREVIOUS_EMAIL", "ohmatt@admin.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", "configured-bootstrap-password")

    extensions.bootstrap_admin_user()

    assert existing_admin.email == "ohmatt160@gmail.com"
    assert existing_admin.password_hash == "existing-password-hash"
    assert database.commits == 1


def test_bootstrap_admin_replaces_precreated_target_and_preserves_original(monkeypatch):
    new_admin = SimpleNamespace(
        id=22,
        email="ohmatt160@gmail.com",
        is_admin=True,
        is_verified=True,
        preferences={"currency": "USD"},
        password_hash="new-account-hash",
    )
    original_admin = SimpleNamespace(
        id=1,
        email="ohmatt@admin.com",
        is_admin=True,
        is_verified=True,
        preferences={"currency": "NGN"},
        password_hash="original-password-hash",
    )

    class Query:
        def __init__(self, result):
            self.result = result

        def filter(self, _expression):
            return self

        def first(self):
            return self.result

    class Database:
        results = [new_admin, original_admin]
        commits = 0

        def query(self, _model):
            return Query(self.results.pop(0))

        def flush(self):
            pass

        def commit(self):
            self.commits += 1

    database = Database()
    monkeypatch.setattr(extensions, "db_session", database)
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_EMAIL", "ohmatt160@gmail.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PREVIOUS_EMAIL", "ohmatt@admin.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", "configured-bootstrap-password")

    extensions.bootstrap_admin_user()

    assert original_admin.email == "ohmatt160@gmail.com"
    assert original_admin.password_hash == "original-password-hash"
    assert original_admin.preferences["currency"] == "NGN"
    assert new_admin.email == "inactive-admin-migration-22@invalid.local"
    assert new_admin.is_admin is False
    assert new_admin.preferences["is_active"] is False
    assert database.commits == 1
