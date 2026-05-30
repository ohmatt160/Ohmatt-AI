from sqlalchemy.orm import Session
from app.models.user import User
from app.models.country import Country
from app.models.language import Language
from app.schemas.user import UserCreate
from app.utils.auth import verify_token
from typing import Optional
from fastapi import HTTPException


class UserService:
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already exists")

        username = user_data.username or user_data.email.split('@')[0]

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
            email=user_data.email,
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
        )
        user.set_password(user_data.password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.check_password(password):
            return None
        return user

    @staticmethod
    def verify_user(db: Session, email: str) -> bool:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        user.is_verified = True
        db.commit()
        return True
