from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.models.country import Country
from app.models.language import Language
from app.schemas.user import UserCreate
from app.utils.auth import verify_token
from typing import Optional
from fastapi import HTTPException
from app.config import settings


class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate, *, commit: bool = True) -> User:
        email = user_data.email.strip().lower()
        existing = db.query(User).filter(func.lower(User.email) == email).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please sign in instead.",
            )

        username = (user_data.username or email.split('@')[0]).strip()
        if db.query(User).filter(func.lower(User.username) == username.lower()).first():
            username = f"{username}-{email.split('@')[1].split('.')[0]}"

        country = None
        if user_data.country_id and str(user_data.country_id).isdigit():
            country = db.query(Country).filter(Country.id == int(user_data.country_id)).first()
        if not country and user_data.country:
            country = db.query(Country).filter(Country.code == user_data.country.upper()).first()

        language = None
        if user_data.language_id and str(user_data.language_id).isdigit():
            language = db.query(Language).filter(Language.id == int(user_data.language_id)).first()
        if not language:
            language_code = country.language if country else "en"
            language = db.query(Language).filter(Language.code == language_code).first()

        currency = user_data.currency or (country.currency if country else "USD")

        user = User(
            username=username,
            email=email,
            country_id=country.id if country else None,
            language_id=language.id if language else None,
            timezone=user_data.timezone or "UTC",
            preferences={
                "currency": currency,
                "date_format": "YYYY-MM-DD",
                "notifications": True,
                "email_alerts": True,
                "transaction_alerts": True,
                "two_factor_enabled": False,
            },
            is_admin=email in settings.admin_emails,
            is_verified=email in settings.admin_emails,
        )
        user.set_password(user_data.password)
        try:
            db.add(user)
            if commit:
                db.commit()
                db.refresh(user)
            else:
                db.flush()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="An account with this email already exists. Please sign in instead.",
            )
        return user

    @staticmethod
    def authenticate_user(db: Session, login: str, password: str) -> Optional[User]:
        normalized_login = login.strip().lower()
        user = db.query(User).filter(
            or_(
                User.email == normalized_login,
                User.username == login.strip(),
            )
        ).first()
        if not user or not user.check_password(password):
            return None
        if (user.preferences or {}).get("is_active", True) is False:
            return None
        if user.email and user.email.lower() in settings.admin_emails and not user.is_admin:
            user.is_admin = True
            user.is_verified = True
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def verify_user(db: Session, email: str) -> bool:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        user.is_verified = True
        db.commit()
        return True
