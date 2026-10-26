import pytest
from types import SimpleNamespace
from pydantic import ValidationError

from app.schemas.user import ProfileUpdate, UserCreate
from app.models.country import Country
from app.models.language import Language
from app.services.user_service import UserService


def test_profile_country_accepts_iso_code():
    update = ProfileUpdate(country="ng")

    assert update.country == "ng"


def test_profile_country_rejects_country_name():
    with pytest.raises(ValidationError):
        ProfileUpdate(country="Nigeria")


def test_registration_requires_iso_country_code():
    with pytest.raises(ValidationError):
        UserCreate(email="new@example.com", password="StrongPass123")

    user = UserCreate(
        email="new@example.com",
        password="StrongPass123",
        country="ng",
    )
    assert user.country == "ng"

    with pytest.raises(ValidationError):
        UserCreate(
            email="new@example.com",
            password="StrongPass123",
            country="Nigeria",
        )


def test_registration_uses_country_currency_and_timezone(monkeypatch):
    country = SimpleNamespace(id=10, code="NG", language="en", currency="NGN", timezone="Africa/Lagos")
    language = SimpleNamespace(id=1)

    class FakeUser:
        email = "email"
        username = "username"

        def __init__(self, **values):
            self.__dict__.update(values)

        def set_password(self, _password):
            self.password_hash = "hashed"

    monkeypatch.setattr("app.services.user_service.User", FakeUser)

    class Query:
        def __init__(self, model):
            self.model = model

        def filter(self, *_args):
            return self

        def first(self):
            if self.model is Country:
                return country
            if self.model is Language:
                return language
            return None

    class Database:
        def query(self, model):
            return Query(model)

        def add(self, user):
            pass

        def commit(self):
            pass

        def refresh(self, user):
            pass

    registration = UserCreate(
        email="new@example.com",
        password="StrongPass123",
        country="ng",
        currency="USD",
        timezone="UTC",
    )

    created = UserService.create_user(Database(), registration)

    assert created.country_id == 10
    assert created.timezone == "Africa/Lagos"
    assert created.preferences["currency"] == "NGN"
