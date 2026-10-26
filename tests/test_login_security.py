from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.routes.auth import issue_2fa_code, verify_2fa_code
from app.schemas.user import ProfileUpdate


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
