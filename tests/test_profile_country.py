import pytest
from pydantic import ValidationError

from app.schemas.user import ProfileUpdate


def test_profile_country_accepts_iso_code():
    update = ProfileUpdate(country="ng")

    assert update.country == "ng"


def test_profile_country_rejects_country_name():
    with pytest.raises(ValidationError):
        ProfileUpdate(country="Nigeria")
