import smtplib
import secrets
import hashlib
import hmac
import logging
import time
from email.mime.text import MIMEText
from urllib.parse import urlencode
import requests

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status, Form
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Optional
from datetime import datetime, timedelta

from app.config import settings
from app.extensions import get_db
from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    VerifyRequest,
    LoginRequest,
    ProfileUpdate,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TwoFactorVerifyRequest,
    TwoFactorDisableRequest,
    LoginEmailResendRequest,
)
from app.services.user_service import UserService
from app.services.integration_outbox_service import enqueue_notification, should_route_to_ohmattos
from app.utils.auth import create_access_token, decode_token_payload, verify_token, get_current_user, get_request_token, confirm_token, \
    generate_token  # Added confirm_token
from app.utils.i18n import t, user_language
from app.models.user import User
from app.models.blacklist import Blacklist
from app.models.session import UserSession
from app.schemas.user import LoginRequest
from app.middleware.activity import log_activity

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("ohmatt.auth")


def request_client_ip(request: Request) -> Optional[str]:
    peer_ip = request.client.host if request.client else None
    if peer_ip in settings.trusted_proxy_ips:
        forwarded = request.headers.get("x-forwarded-for", "").split(",")
        if forwarded and forwarded[0].strip():
            return forwarded[0].strip()
    return peer_ip
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
        ip_address=request_client_ip(request) if request else None,
        user_agent=request.headers.get("user-agent")[:500] if request else None,
    )
    db.add(session)
    db.commit()


def is_known_device(db: Session, user: User, request: Request) -> bool:
    """Match both network address and browser signature to a prior session."""
    client_ip = request_client_ip(request)
    user_agent = (request.headers.get("user-agent") or "")[:500]
    if not client_ip or not user_agent:
        return False
    return db.query(UserSession.id).filter(
        UserSession.user_id == user.id,
        UserSession.ip_address == client_ip,
        UserSession.user_agent == user_agent,
    ).first() is not None


def verify_login_challenge(db: Session, user: User, request: Request, code: Optional[str]) -> None:
    preferences = dict(user.preferences or {})
    has_prior_sessions = db.query(UserSession.id).filter(UserSession.user_id == user.id).first() is not None
    new_device = (
        settings.RISK_BASED_LOGIN_CHALLENGE_ENABLED
        and (not has_prior_sessions or not is_known_device(db, user, request))
    )
    needs_challenge = bool(preferences.get("two_factor_enabled") or new_device or user.is_admin)
    if not needs_challenge:
        return
    if not user.is_verified and settings.EMAIL_VERIFICATION_REQUIRED:
        raise HTTPException(status_code=403, detail="Verify your email before completing sign-in verification")
    if not code:
        current_preferences = user.preferences or {}
        if has_active_2fa_challenge(current_preferences):
            raise HTTPException(status_code=428, detail="Two-factor code required")
        send_login_challenge(db, user)
        raise HTTPException(status_code=428, detail="Two-factor code required")
    if not verify_2fa_code(user, code):
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db.commit()


def login_challenge_required(db: Session, user: User, request: Request) -> bool:
    has_prior_sessions = db.query(UserSession.id).filter(UserSession.user_id == user.id).first() is not None
    new_device = (
        settings.RISK_BASED_LOGIN_CHALLENGE_ENABLED
        and (not has_prior_sessions or not is_known_device(db, user, request))
    )
    return bool((user.preferences or {}).get("two_factor_enabled") or new_device or user.is_admin)


def _resend_cooldown_remaining(user: User, key: str, cooldown_seconds: int = 30) -> int:
    try:
        last_sent = float((user.preferences or {}).get(key) or 0)
    except (TypeError, ValueError):
        last_sent = 0
    return max(0, int(cooldown_seconds - (time.time() - last_sent))) if last_sent else 0


def _store_resend_timestamp(user: User, key: str) -> None:
    preferences = dict(user.preferences or {})
    preferences[key] = time.time()
    user.preferences = preferences


def send_login_challenge(db: Session, user: User, *, enforce_cooldown: bool = False) -> None:
    if enforce_cooldown:
        wait_seconds = _resend_cooldown_remaining(user, "login_challenge_last_sent_at")
        if wait_seconds:
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {wait_seconds} seconds before requesting another sign-in code.",
                headers={"Retry-After": str(wait_seconds)},
            )
    code = issue_2fa_code(user)
    preferences = dict(user.preferences or {})
    preferences["login_challenge_last_sent_at"] = time.time()
    user.preferences = preferences
    challenge_expiry = int(preferences.get("two_factor_expires_at") or 0)
    # Security codes must use direct email delivery; enqueue acceptance is not proof
    # that the recipient's mailbox has received the code.
    delivered = send_plain_email(
        user.email,
        "Your Ohmatt sign-in code",
        f"Your sign-in code is {code}. It expires in 10 minutes.",
    )
    db.commit()
    if not delivered:
        preferences = dict(user.preferences or {})
        preferences.pop("two_factor_code_hash", None)
        preferences.pop("two_factor_expires_at", None)
        user.preferences = preferences
        db.commit()
        logger.error("Login challenge email delivery failed user_id=%s challenge_expiry=%s", user.id, challenge_expiry)
        raise HTTPException(status_code=503, detail="Sign-in verification email could not be sent. Please try again later.")


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


def classify_sendgrid_failure(status_code: int, response_text: str) -> str:
    response_hint = (response_text or "").lower()
    if status_code == 401:
        if any(hint in response_hint for hint in ("maximum credits exceeded", "credit limit", "credits exceeded")):
            return "free_trial_credit_limit"
        return "invalid_api_key_or_permissions"
    if status_code == 403 and any(
        hint in response_hint for hint in ("sender", "from address", "verified")
    ):
        return "sender_identity_not_verified"
    if status_code == 403:
        return "account_restricted_or_not_unlocked"
    if status_code == 429:
        return "provider_rate_limited"
    return "provider_rejected_request"


def send_sendgrid_email(email: str, subject: str, body: str) -> bool:
    if not settings.SENDGRID_API_KEY or not settings.SENDGRID_FROM_EMAIL:
        logger.error(
            "SendGrid auth email is not configured api_key_present=%s sender_present=%s",
            bool(settings.SENDGRID_API_KEY),
            bool(settings.SENDGRID_FROM_EMAIL),
        )
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
        if 200 <= response.status_code < 300:
            logger.info("SendGrid accepted auth email status=%s", response.status_code)
            return True
        failure_reason = classify_sendgrid_failure(response.status_code, response.text)
        logger.error("SendGrid rejected auth email status=%s reason=%s", response.status_code, failure_reason)
        return False
    except requests.RequestException:
        logger.exception("SendGrid auth email request failed")
        return False


def send_brevo_email(email: str, subject: str, body: str) -> bool:
    if not settings.BREVO_API_KEY or not settings.BREVO_FROM_EMAIL:
        logger.error(
            "Brevo auth email is not configured api_key_present=%s sender_present=%s",
            bool(settings.BREVO_API_KEY),
            bool(settings.BREVO_FROM_EMAIL),
        )
        return False

    payload = {
        "sender": {"email": settings.BREVO_FROM_EMAIL, "name": settings.BREVO_FROM_NAME},
        "to": [{"email": email}],
        "subject": subject,
        "textContent": body,
    }
    try:
        response = requests.post(
            settings.BREVO_API_URL,
            json=payload,
            headers={"api-key": settings.BREVO_API_KEY, "Content-Type": "application/json"},
            timeout=10,
        )
        if 200 <= response.status_code < 300:
            logger.info("Brevo accepted auth email status=%s", response.status_code)
            return True
        # Do not log provider response bodies: they may contain recipient or account details.
        logger.error("Brevo rejected auth email status=%s", response.status_code)
        return False
    except requests.RequestException:
        logger.exception("Brevo auth email request failed")
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
    if settings.BREVO_API_KEY:
        return send_brevo_email(email, subject, body)
    if send_sendgrid_email(email, subject, body):
        return True
    if not settings.is_production:
        return send_smtp_email(email, subject, body)
    return False


def deliver_auth_email(
    db: Session,
    user: User,
    *,
    purpose: str,
    subject: str,
    body: str,
    idempotency_key: str,
) -> bool:
    if should_route_to_ohmattos(user_id=user.id, email=user.email):
        enqueue_notification(
            db,
            user_id=user.id,
            purpose=purpose,
            channel_type="email",
            content={"to": user.email, "subject": subject, "body": body},
            idempotency_key=idempotency_key,
        )
        return True
    return send_plain_email(user.email, subject, body)


def issue_2fa_code(user: User) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    preferences = dict(user.preferences or {})
    preferences["two_factor_code_hash"] = hashlib.sha256(code.encode()).hexdigest()
    preferences["two_factor_expires_at"] = (time.time() + 600)
    user.preferences = preferences
    return code


def verify_2fa_code(user: User, code: str) -> bool:
    preferences = dict(user.preferences or {})
    try:
        expires_at = float(preferences.get("two_factor_expires_at") or 0)
    except (TypeError, ValueError):
        return False
    expected_hash = preferences.get("two_factor_code_hash")
    supplied_hash = hashlib.sha256((code or "").encode()).hexdigest()
    valid = bool(expected_hash) and hmac.compare_digest(expected_hash, supplied_hash) and time.time() <= expires_at
    if valid:
        preferences.pop("two_factor_code_hash", None)
        preferences.pop("two_factor_expires_at", None)
        user.preferences = preferences
    return valid


def has_active_2fa_challenge(preferences: dict) -> bool:
    if not isinstance(preferences.get("two_factor_code_hash"), str):
        return False
    try:
        return time.time() <= float(preferences.get("two_factor_expires_at") or 0)
    except (TypeError, ValueError):
        return False


@router.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    validate_password_strength(user.password)
    created_user = UserService.create_user(db, user, commit=False)
    if settings.EMAIL_VERIFICATION_REQUIRED:
        token = generate_token(created_user.email)
        verify_url = f"{settings.FRONTEND_URL.rstrip()}/verify?{urlencode({'token': token})}"
        verification_subject = "Verify your Ohmatt account"
        verification_body = f"Welcome to Ohmatt.\n\nVerify your email here: {verify_url}"
        if should_route_to_ohmattos(user_id=created_user.id, email=created_user.email):
            enqueue_notification(
                db,
                user_id=created_user.id,
                purpose="email-verification",
                channel_type="email",
                content={
                    "to": created_user.email,
                    "subject": verification_subject,
                    "body": verification_body,
                },
                idempotency_key=f"user:{created_user.id}:email-verification:registration",
            )
        else:
            background_tasks.add_task(
                send_plain_email,
                created_user.email,
                verification_subject,
                verification_body,
            )
    log_activity(db,
        request,
        created_user.id,
        "registration",
        entity_type="user",
        entity_id=created_user.id,
        description="User registered",
        commit=False,
    )
    db.commit()
    db.refresh(created_user)
    return serialize_user(created_user)


@router.post("/login", response_model=Token)
def login_user(data: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    verify_login_challenge(db, user, request, data.two_factor_code)
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


@router.post("/login/resend")
def resend_login_email(data: LoginEmailResendRequest, request: Request, db: Session = Depends(get_db)):
    """Resend verification or sign-in email after revalidating the password."""
    user = UserService.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_verified and settings.EMAIL_VERIFICATION_REQUIRED:
        wait_seconds = _resend_cooldown_remaining(user, "verification_email_last_sent_at", 60)
        if wait_seconds:
            raise HTTPException(
                status_code=429,
                detail=f"Please wait {wait_seconds} seconds before requesting another verification email.",
                headers={"Retry-After": str(wait_seconds)},
            )
        token = generate_token(user.email)
        verify_url = f"{settings.FRONTEND_URL.rstrip('/')}/verify?{urlencode({'token': token})}"
        _store_resend_timestamp(user, "verification_email_last_sent_at")
        delivered = send_plain_email(
            user.email,
            "Verify your Ohmatt account",
            f"Verify your email here: {verify_url}",
        )
        db.commit()
        if not delivered:
            logger.error("Email verification delivery failed user_id=%s", user.id)
            raise HTTPException(status_code=503, detail="Verification email could not be sent. Please try again later.")
        return {"kind": "email_verification", "message": "Verification email sent. Check your inbox and spam folder."}

    if not login_challenge_required(db, user, request):
        raise HTTPException(status_code=400, detail="This account does not currently need a sign-in code")

    send_login_challenge(db, user, enforce_cooldown=True)
    return {"kind": "two_factor", "message": "A fresh sign-in code was sent. Check your inbox and spam folder."}

@router.post("/login/form", response_model=Token, include_in_schema=False)
def login_form(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    two_factor_code: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    user = UserService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    verify_login_challenge(db, user, request, two_factor_code)
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
    db.query(User.id).filter(User.id == current_user.id).with_for_update().one()
    from app.models.bank_account import BankAccount
    from app.models.bank_connection import BankConnection
    from app.models.bank_transaction import BankTransaction
    from app.models.finance import Budget, RecurringTransaction, TransactionCategory, TransactionReceipt
    from app.models.insight import Insight
    from app.models.messages import Messages
    from app.models.ai_memory import AIPersonalMemory
    from app.models.transaction import Transaction

    db.query(TransactionReceipt).filter_by(user_id=current_user.id).delete()
    db.query(Budget).filter_by(user_id=current_user.id).delete()
    db.query(RecurringTransaction).filter_by(user_id=current_user.id).delete()
    db.query(TransactionCategory).filter_by(user_id=current_user.id).delete()
    db.query(Insight).filter_by(user_id=current_user.id).delete()
    db.query(AIPersonalMemory).filter_by(user_id=current_user.id).delete()
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
    challenge_expiry = int((current_user.preferences or {}).get("two_factor_expires_at") or 0)
    deliver_auth_email(
        db,
        current_user,
        purpose="two-factor-enrollment",
        subject="Confirm Ohmatt two-factor authentication",
        body=f"Your confirmation code is {code}.",
        idempotency_key=f"user:{current_user.id}:2fa-enrollment:{challenge_expiry}",
    )
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
    data: TwoFactorDisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.check_password(data.current_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    preferences = dict(current_user.preferences or {})
    preferences["two_factor_enabled"] = False
    preferences.pop("two_factor_code", None)
    preferences.pop("two_factor_code_hash", None)
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
        reset_body = "\n".join(
            [
                "You requested a password reset for your Ohmatt account.",
                "",
                f"Reset your password here: {reset_url}",
                "",
                "This link expires in 24 hours. If you did not request this, you can ignore this email.",
            ]
        )
        token_fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()[:24]
        deliver_auth_email(
            db,
            user,
            purpose=PASSWORD_RESET_PURPOSE,
            subject="Reset your Ohmatt password",
            body=reset_body,
            idempotency_key=f"user:{user.id}:password-reset:{token_fingerprint}",
        )
        if settings.OHMATTOS_ENABLED:
            db.commit()
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
