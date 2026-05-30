from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.extensions import get_db
from app.models.user import User
from app.config import settings
from itsdangerous import URLSafeTimedSerializer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Check blacklist
    from app.models.blacklist import Blacklist
    from app.extensions import db_session
    if db_session.query(Blacklist).filter_by(jti=token).first():
        raise HTTPException(status_code=401, detail="Token revoked")

    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def generate_token(email: str) -> str:
    """Generate a verification token for email"""
    serializer = URLSafeTimedSerializer(settings.JWT_SECRET_KEY)
    return serializer.dumps(email, salt="email-verification")

def confirm_token(token: str, expiration: int = 86400) -> Optional[str]:
    """Confirm a verification token (default 24 hours)"""
    serializer = URLSafeTimedSerializer(settings.JWT_SECRET_KEY)
    try:
        email = serializer.loads(token, salt="email-verification", max_age=expiration)
        return email
    except:
        return None