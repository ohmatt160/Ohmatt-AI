import smtplib
import random
import time
from email.mime.text import MIMEText
from urllib.parse import urlencode
import requests

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta

from app.config import settings
from app.extensions import get_db
from app.schemas.user import UserCreate, UserResponse, Token, VerifyRequest, LoginRequest, ProfileUpdate, \
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest, TwoFactorVerifyRequest
from app.services.user_service import UserService
from app.utils.auth import create_access_token, decode_token_payload, verify_token, get_current_user, get_request_token, confirm_token, \
    generate_token  # Added confirm_token
from app.utils.i18n import t, user_language
from app.models.user import User
from app.models.blacklist import Blacklist
from app.models.session import UserSession
from app.schemas.user import LoginRequest
from app.middleware.activity import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
PASSWORD_RESET_PURPOSE = "password-reset"

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


def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key=settings.AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )


def clear_auth_cookie(response: Response):
    response.delete_cookie(
        key=settings.AUTH_COOKIE_NAME,
        path="/",
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def create_user_session(db: Session, user: User, token: str, request: Optional[Request] = None) -> None:
    payload = decode_token_payload(token) or {}
    token_jti = payload.get("jti")
    if not token_jti:
        return
    session = UserSession(
        user_id=user.id,
        token_jti=token_jti,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent")[:500] if request else None,
    )
    db.add(session)
    db.commit()


def revoke_current_session(db: Session, token: Optional[str], user_id: int) -> None:
    now = datetime.utcnow()
    if token:
        payload = decode_token_payload(token) or {}
        token_jti = payload.get("jti")
        if token_jti:
            session = db.query(UserSession).filter_by(token_jti=token_jti, user_id=user_id).first()
            if session:
                session.is_active = False
                session.revoked_at = now
    db.commit()


def validate_password_strength(password: str):
    common_passwords = {
        "password",
        "password1",
        "password123",
        "12345678",
        "qwerty123",
        "admin123",
        "letmein1",
        "welcome1",
        "iloveyou1",
    }
    if password.strip().lower() in common_passwords:
        raise HTTPException(400, "Password is too common")
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
    return send_plain_email(
        email,
        "Reset your Ohmatt password",
        "\n".join(
            [
                "You requested a password reset for your Ohmatt account.",
                "",
                f"Reset your password here: {reset_url}",
                "",
                "This link expires in 24 hours. If you did not request this, you can ignore this email.",
            ]
        ),
    )


def send_sendgrid_email(email: str, subject: str, body: str) -> bool:
    if not settings.SENDGRID_API_KEY or not settings.SENDGRID_FROM_EMAIL:
        return False

    payload = {
        "personalizations": [
            {
                "to": [{"email": email}],
                "subject": subject,
            }
        ],
        "from": {
            "email": settings.SENDGRID_FROM_EMAIL,
            "name": settings.SENDGRID_FROM_NAME,
        },
        "content": [
            {
                "type": "text/plain",
                "value": body,
            }
        ],
    }
    headers = {
        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            settings.SENDGRID_API_URL,
            json=payload,
            headers=headers,
            timeout=10,
        )
        return 200 <= response.status_code < 300
    except requests.RequestException:
        return False


def send_smtp_email(email: str, subject: str, body: str) -> bool:
    if not settings.MAIL_SERVER or not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
        return False
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.MAIL_USERNAME
    message["To"] = email
    try:
        if settings.MAIL_USE_SSL:
            with smtplib.SMTP_SSL(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10) as smtp:
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10) as smtp:
                if settings.MAIL_USE_TLS:
                    smtp.starttls()
                smtp.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                smtp.send_message(message)
        return True
    except Exception:
        return False


def send_plain_email(email: str, subject: str, body: str) -> bool:
    if send_sendgrid_email(email, subject, body):
        return True
    if not settings.is_production:
        return send_smtp_email(email, subject, body)
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
def register_user(
    user: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    validate_password_strength(user.password)
    created_user = UserService.create_user(db, user)
    token = generate_token(created_user.email)
    verify_url = f"{settings.FRONTEND_URL.rstrip()}/verify?{urlencode({'token': token})}"
    background_tasks.add_task(
        send_plain_email,
        created_user.email,
        "Verify your Ohmatt account",
        f"Welcome to Ohmatt.\n\nVerify your email here: {verify_url}",
    )
    log_activity(db,
        request,
        created_user.id,
        "registration",
        entity_type="user",
        entity_id=created_user.id,
        description="User registered",
    )
    return serialize_user(created_user)


@router.post("/login", response_model=Token)
def login_user(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    preferences = dict(user.preferences or {})
    if preferences.get("two_factor_enabled"):
        if not data.two_factor_code:
            code = issue_2fa_code(user)
            db.commit()
            send_plain_email(user.email, "Your Ohmatt sign-in code", f"Your sign-in code is {code}. It expires in 10 minutes.")
            raise HTTPException(status_code=428, detail="Two-factor code required")
        if not verify_2fa_code(user, data.two_factor_code):
            db.commit()
            raise HTTPException(status_code=401, detail="Invalid credentials")
        db.commit()
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    create_user_session(db, user, access_token, request)
    set_auth_cookie(response, access_token)
    log_activity(db,
        request,
        user.id,
        "login",
        entity_type="user",
        entity_id=user.id,
        description="User logged in",
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/form", response_model=Token, include_in_schema=False)
def login_form(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token(data={"sub": user.email}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    create_user_session(db, user, access_token, request)
    set_auth_cookie(response, access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    token = get_request_token(request, token)
    payload = decode_token_payload(token) if token else None
    token_jti = payload.get("jti") if payload else None
    if token_jti:
        db.add(Blacklist(jti=token_jti, user_id=current_user.id))
    revoke_current_session(db, token, current_user.id)
    clear_auth_cookie(response)
    log_activity(db, request, current_user.id, "logout", entity_type="user", entity_id=current_user.id, description="User logged out")
    return {"message": t("logged_out", lang=user_language(current_user))}


@router.post("/logout-everywhere")
def logout_everywhere(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    sessions = db.query(UserSession).filter_by(user_id=current_user.id, is_active=True).all()
    for session in sessions:
        session.is_active = False
        session.revoked_at = now
    db.commit()
    clear_auth_cookie(response)
    log_activity(db,
        request,
        current_user.id,
        "logout_everywhere",
        entity_type="user",
        entity_id=current_user.id,
        description="User logged out from all sessions",
    )
    return {"message": t("logged_out_everywhere", lang=user_language(current_user))}


@router.post("/refresh", response_model=Token)
def refresh_session(
    request: Request,
    response: Response,
    token: Optional[str] = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = get_request_token(request, token)
    revoke_current_session(db, token, current_user.id)
    access_token = create_access_token(
        data={"sub": current_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    create_user_session(db, current_user, access_token, request)
    set_auth_cookie(response, access_token)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verify")
def verify_account(data: VerifyRequest, db: Session = Depends(get_db)):
    email = confirm_token(data.token)
    if not email:
        raise HTTPException(400, "Invalid or expired token")

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(400, "Invalid or expired token")
    if user.is_verified:
        return {"message": t("account_already_verified", lang=user_language(user))}

    user.is_verified = True
    db.commit()
    return {"message": t("account_verified", lang=user_language(user))}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)

@router.put("/me", response_model=UserResponse)
def update_profile(
    data: ProfileUpdate,
    request: Request,
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
        "language",
        "locale",
    }
    preferences = dict(current_user.preferences or {})

    if "country" in update_data or "country_id" in update_data:
        from app.models.country import Country

        country_code = update_data.pop("country", None)
        country_id = update_data.pop("country_id", None)
        if country_code:
            country = db.query(Country).filter_by(code=country_code.upper()).first()
        else:
            try:
                country = db.get(Country, int(country_id))
            except (TypeError, ValueError) as exc:
                raise HTTPException(400, "Invalid country") from exc
        if not country:
            raise HTTPException(400, "Invalid country")
        current_user.country_id = country.id
        current_user.timezone = country.timezone or current_user.timezone
        preferences["currency"] = country.currency or preferences.get("currency", "USD")
        current_user.preferences = preferences

    for field, value in update_data.items():
        if field in preference_fields:
            preferences[field] = value
            continue
        setattr(current_user, field, value)

    if any(field in update_data for field in preference_fields):
        current_user.preferences = preferences

    db.commit()
    db.refresh(current_user)
    log_activity(db,
        request,
        current_user.id,
        "profile_update",
        entity_type="user",
        entity_id=current_user.id,
        description="Profile updated",
        metadata={"fields": list(update_data.keys())},
    )
    return serialize_user(current_user)

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    if not current_user.check_password(data.current_password):
        raise HTTPException(400, "Invalid credentials")
    validate_password_strength(data.new_password)
    current_user.set_password(data.new_password)
    db.commit()
    log_activity(db, request, current_user.id, "password_change", entity_type="user", entity_id=current_user.id, description="Password changed")
    return {"message": t("password_changed", lang=user_language(current_user))}


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
    return {"message": t("account_deleted", lang=user_language(current_user))}


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
    return {"message": t("confirmation_code_sent", lang=user_language(current_user))}


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
    response = {"message": t("password_reset_requested")}

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
        raise HTTPException(400, "Invalid or expired token")
    validate_password_strength(data.new_password)
    user.set_password(data.new_password)
    db.commit()
    return {"message": t("password_reset_success", lang=user_language(user))}
