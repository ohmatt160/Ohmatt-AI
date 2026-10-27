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

    database = Database()
    monkeypatch.setattr(extensions, "db_session", database)
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_EMAIL", "ohmatt160@gmail.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PREVIOUS_EMAIL", "ohmatt@admin.com")
    monkeypatch.setattr(settings, "BOOTSTRAP_ADMIN_PASSWORD", "configured-bootstrap-password")

    extensions.bootstrap_admin_user()

    assert existing_admin.email == "ohmatt160@gmail.com"
    assert existing_admin.password_hash == "existing-password-hash"
    assert database.commits == 1
