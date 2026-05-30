from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Optional
from datetime import timedelta

from app.extensions import get_db, db_session
from app.schemas.user import UserCreate, UserResponse, Token, VerifyRequest, LoginRequest, ProfileUpdate, \
    ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services.user_service import UserService
from app.utils.auth import create_access_token, verify_token, get_current_user, confirm_token, \
    generate_token  # Added confirm_token
from app.models.user import User
from app.models.blacklist import Blacklist
from app.schemas.user import LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    return UserService.create_user(db, user)


@router.post("/login", response_model=Token)
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
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
    return current_user

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
    return current_user

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    if not current_user.check_password(data.current_password):
        raise HTTPException(400, "Current password is incorrect")
    current_user.set_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}


@router.post("/password-reset/request")
def request_password_reset(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset email"""
    user = db_session.query(User).filter_by(email=data.email).first()
    if user:
        token = generate_token(user.email)
        # TODO: Send email with token
        # send_email(user.email, "Password Reset", f"Your token: {token}")
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/password-reset/confirm")
def confirm_password_reset(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token"""
    email = confirm_token(data.token)
    if not email:
        raise HTTPException(400, "Invalid or expired token")
    user = db_session.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")
    user.set_password(data.new_password)
    db_session.commit()
    return {"message": "Password reset successfully"}
