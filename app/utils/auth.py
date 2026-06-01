from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.extensions import get_db
from app.models.user import User
from app.config import settings
from itsdangerous import URLSafeTimedSerializer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire, "jti": to_encode.get("jti") or uuid4().hex})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")

def decode_token_payload(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        return None

def verify_token(token: str) -> Optional[str]:
    payload = decode_token_payload(token)
    if not payload:
        return None
    return payload.get("sub")


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    token = token or request.cookies.get(settings.AUTH_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Check blacklist
    from app.models.blacklist import Blacklist
    from app.models.session import UserSession
    if db.query(Blacklist).filter_by(jti=token).first():
        raise HTTPException(status_code=401, detail="Token revoked")

    payload = decode_token_payload(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload.get("sub")
    token_jti = payload.get("jti")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if token_jti:
        session = (
            db.query(UserSession)
            .filter(
                UserSession.token_jti == token_jti,
                UserSession.user_id == user.id,
                UserSession.is_active == True,
                UserSession.revoked_at.is_(None),
            )
            .first()
        )
        if not session:
            raise HTTPException(status_code=401, detail="Session expired")
        now = datetime.utcnow()
        idle_timeout = timedelta(minutes=settings.SESSION_IDLE_TIMEOUT_MINUTES)
        if session.last_seen_at and now - session.last_seen_at > idle_timeout:
            session.is_active = False
            session.revoked_at = now
            db.commit()
            raise HTTPException(status_code=401, detail="Session expired")
        session.last_seen_at = now
        db.commit()
    return user

def generate_token(email: str, purpose: str = "email-verification") -> str:
    """Generate a signed token for an email-scoped action."""
    serializer = URLSafeTimedSerializer(settings.JWT_SECRET_KEY)
    return serializer.dumps(email, salt=purpose)

def confirm_token(
    token: str,
    expiration: int = 86400,
    purpose: str = "email-verification",
) -> Optional[str]:
    """Confirm a signed email token."""
    serializer = URLSafeTimedSerializer(settings.JWT_SECRET_KEY)
    try:
        email = serializer.loads(token, salt=purpose, max_age=expiration)
        return email
    except:
        return None
