import smtplib
import random
import time
from email.mime.text import MIMEText
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Optional
from datetime import timedelta

from app.config import settings
from app.extensions import get_db, db_session
from app.schemas.user import UserCreate, UserResponse, Token, VerifyRequest, LoginRequest, ProfileUpdate, \
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, TwoFactorVerifyRequest
from app.services.user_service import UserService
from app.utils.auth import create_access_token, verify_token, get_current_user, confirm_token, \
    generate_token  # Added confirm_token
from app.models.user import User
from app.models.blacklist import Blacklist
from app.schemas.user import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
PASSWORD_RESET_PURPOSE = "password-reset"
AUTH_RATE_LIMIT: dict[str, list[float]] = {}
AUTH_RATE_LIMIT_WINDOW = 60
AUTH_RATE_LIMIT_MAX = 10


def serialize_user(user: User) -> dict:
    preferences = user.preferences or {}
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "country_id": str(user.country_id) if user.country_id is not None else None,
        "language_id": str(user.language_id) if user.language_id is not None else None,
        "timezone": user.timezone,
        "preferences": preferences,
        "is_admin": user.is_admin,
        "is_verified": user.is_verified,
        "currency": preferences.get("currency"),
        "created_at": None,
        "is_active": preferences.get("is_active", True),
    }


def check_auth_rate_limit(request: Request):
    key = request.client.host if request.client else "unknown"
    now = time.time()
    hits = [hit for hit in AUTH_RATE_LIMIT.get(key, []) if now - hit < AUTH_RATE_LIMIT_WINDOW]
    if len(hits) >= AUTH_RATE_LIMIT_MAX:
        raise HTTPException(429, "Too many auth attempts. Please wait a minute and try again.")
    hits.append(now)
    AUTH_RATE_LIMIT[key] = hits


def validate_password_strength(password: str):
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if not re_search(r"[A-Z]", password):
        raise HTTPException(400, "Password must include an uppercase letter")
    if not re_search(r"[a-z]", password):
        raise HTTPException(400, "Password must include a lowercase letter")
    if not re_search(r"\d", password):
        raise HTTPException(400, "Password must include a number")


def re_search(pattern: str, value: str) -> bool:
    import re
    return bool(re.search(pattern, value))


def build_password_reset_url(token: str) -> str:
    base_url = settings.FRONTEND_URL.rstrip("/")
    return f"{base_url}/reset-password?{urlencode({'token': token})}"


def send_password_reset_email(email: str, reset_url: str) -> bool:
    if not settings.MAIL_SERVER or not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        return False

    message = MIMEText(
        "\n".join(
            [
                "You requested a password reset for your Ohmatt account.",
                "",
                f"Reset your password here: {reset_url}",
                "",
                "This link expires in 24 hours. If you did not request this, you can ignore this email.",
            ]
        )
    )
    message["Subject"] = "Reset your Ohmatt password"
    message["From"] = settings.MAIL_USERNAME
    message["To"] = email

    try:
        if settings.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
                if settings.MAIL_USE_TLS:
                    smtp.starttls()
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                smtp.send_message(message)
        return True
    except Exception:
        return False


def send_plain_email(email: str, subject: str, body: str) -> bool:
    if not settings.MAIL_SERVER or not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        return False
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.MAIL_USERNAME
    message["To"] = email
    try:
        if settings.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as smtp:
                if settings.MAIL_USE_TLS:
                    smtp.starttls()
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                smtp.send_message(message)
        return True
    except Exception:
        return False


def issue_2fa_code(user: User) -> str:
    code = f"{random.randint(0, 999999):06d}"
    preferences = dict(user.preferences or {})
    preferences["two_factor_code"] = code
    preferences["two_factor_expires_at"] = (time.time() + 600)
    user.preferences = preferences
    return code


def verify_2fa_code(user: User, code: str) -> bool:
    preferences = dict(user.preferences or {})
    expires_at = float(preferences.get("two_factor_expires_at") or 0)
    valid = preferences.get("two_factor_code") == code and time.time() <= expires_at
    if valid:
        preferences.pop("two_factor_code", None)
        preferences.pop("two_factor_expires_at", None)
        user.preferences = preferences
    return valid


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    check_auth_rate_limit(request)
    validate_password_strength(user.password)
    created_user = UserService.create_user(db, user)
    token = generate_token(created_user.email)
    verify_url = f"{settings.FRONTEND_URL.rstrip()}/verify?{urlencode({'token': token})}"
    send_plain_email(
        created_user.email,
        "Verify your Ohmatt account",
        f"Welcome to Ohmatt.\n\nVerify your email here: {verify_url}",
    )
    return serialize_user(created_user)


@router.post("/login", response_model=Token)
def login_user(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_auth_rate_limit(request)
    user = UserService.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    preferences = dict(user.preferences or {})
    if preferences.get("two_factor_enabled"):
        if not data.two_factor_code:
            code = issue_2fa_code(user)
            db.commit()
            send_plain_email(user.email, "Your Ohmatt sign-in code", f"Your sign-in code is {code}. It expires in 10 minutes.")
            raise HTTPException(status_code=428, detail="Two-factor code required")
        if not verify_2fa_code(user, data.two_factor_code):
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid two-factor code")
        db.commit()
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/form", response_model=Token, include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    blacklisted = Blacklist(jti=token, user_id=current_user.id)
    db_session.add(blacklisted)
    db_session.commit()
    return {"message": "Logged out successfully"}


@router.post("/verify")
def verify_account(data: VerifyRequest, db: Session = Depends(get_db)):
    email = confirm_token(data.token)
    if not email:
        raise HTTPException(400, "Invalid or expired token")

    user = db_session.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_verified:
        return {"message": "Already verified"}

    user.is_verified = True
    db_session.commit()
    return {"message": "Account verified"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)

@router.put("/me", response_model=UserResponse)
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    update_data = data.dict(exclude_unset=True)
    preference_fields = {
        "notifications",
        "email_alerts",
        "two_factor_enabled",
        "transaction_alerts",
        "currency",
        "date_format",
    }
    preferences = dict(current_user.preferences or {})

    for field, value in update_data.items():
        if field in preference_fields:
            preferences[field] = value
            continue
        setattr(current_user, field, value)

    if any(field in update_data for field in preference_fields):
        current_user.preferences = preferences

    db.commit()
    db.refresh(current_user)
    return serialize_user(current_user)

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    if not current_user.check_password(data.current_password):
        raise HTTPException(400, "Current password is incorrect")
    validate_password_strength(data.new_password)
    current_user.set_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.delete("/me")
def delete_own_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete the authenticated user's account and owned records."""
    from app.models.bank_account import BankAccount
    from app.models.bank_connection import BankConnection
    from app.models.bank_transaction import BankTransaction
    from app.models.finance import Budget, RecurringTransaction, TransactionCategory, TransactionReceipt
    from app.models.insight import Insight
    from app.models.messages import Messages
    from app.models.transaction import Transaction

    db.query(TransactionReceipt).filter_by(user_id=current_user.id).delete()
    db.query(Budget).filter_by(user_id=current_user.id).delete()
    db.query(RecurringTransaction).filter_by(user_id=current_user.id).delete()
    db.query(TransactionCategory).filter_by(user_id=current_user.id).delete()
    db.query(Insight).filter_by(user_id=current_user.id).delete()
    db.query(Messages).filter((Messages.sender_id == current_user.id) | (Messages.receiver_id == current_user.id)).delete(synchronize_session=False)
    db.query(Transaction).filter_by(user_id=current_user.id).delete()
    db.query(BankTransaction).filter_by(user_id=current_user.id).delete()
    db.query(BankAccount).filter_by(user_id=current_user.id).delete()
    db.query(BankConnection).filter_by(user_id=current_user.id).delete()
    db.delete(current_user)
    db.commit()
    return {"message": "Account deleted"}


@router.post("/2fa/enable")
def enable_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = dict(current_user.preferences or {})
    code = issue_2fa_code(current_user)
    preferences.update(current_user.preferences or {})
    preferences["two_factor_pending"] = True
    current_user.preferences = preferences
    send_plain_email(current_user.email, "Confirm Ohmatt two-factor authentication", f"Your confirmation code is {code}.")
    db.commit()
    return {"message": "Confirmation code sent"}


@router.post("/2fa/confirm")
def confirm_two_factor(
    data: TwoFactorVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_2fa_code(current_user, data.code):
        db.commit()
        raise HTTPException(400, "Invalid or expired two-factor code")
    preferences = dict(current_user.preferences or {})
    preferences["two_factor_enabled"] = True
    preferences.pop("two_factor_pending", None)
    current_user.preferences = preferences
    db.commit()
    return {"two_factor_enabled": True}


@router.post("/2fa/disable")
def disable_two_factor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = dict(current_user.preferences or {})
    preferences["two_factor_enabled"] = False
    preferences.pop("two_factor_code", None)
    preferences.pop("two_factor_expires_at", None)
    preferences.pop("two_factor_pending", None)
    current_user.preferences = preferences
    db.commit()
    return {"two_factor_enabled": False}


@router.post("/password-reset/request")
def request_password_reset(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email without exposing whether the account exists."""
    email = data.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    response = {"message": "If the email exists, a reset link has been sent"}

    if user:
        token = generate_token(user.email, purpose=PASSWORD_RESET_PURPOSE)
        reset_url = build_password_reset_url(token)
        send_password_reset_email(user.email, reset_url)
        if settings.PASSWORD_RESET_LINK_RESPONSE_ENABLED or not settings.is_production:
            response["reset_url"] = reset_url

    return response

@router.post("/password-reset/confirm")
def confirm_password_reset(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    email = confirm_token(
        data.token,
        expiration=settings.EMAIL_TOKEN_EXPIRATION,
        purpose=PASSWORD_RESET_PURPOSE,
    )
    if not email:
        raise HTTPException(400, "Invalid or expired token")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")
    validate_password_strength(data.new_password)
    user.set_password(data.new_password)
    db.commit()
    return {"message": "Password reset successfully"}
