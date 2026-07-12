from pydantic import BaseModel, Field, EmailStr
from typing import Any, Dict, Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    two_factor_code: Optional[str] = Field(None, min_length=6, max_length=6)

class VerifyRequest(BaseModel):
    token: str

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    country_id: int
    language_id: int
    timezone: str = Field(default="UTC")


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None)
    username: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    currency: Optional[str] = Field("USD")
    timezone: Optional[str] = Field("UTC")
    country_id: Optional[str] = Field(None)
    language_id: Optional[str] = Field(None)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    country_id: Optional[str] = None  # Can be string or int
    language_id: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    is_admin: bool = False
    is_verified: bool = False
    currency: Optional[str] = None
    created_at: Optional[str] = None  # Add this
    is_active: bool = True

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    country_id: Optional[int] = None
    language_id: Optional[int] = None
    timezone: Optional[str] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None

class ProfileUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3)
    email: Optional[str] = None
    country_id: Optional[str] = None
    country: Optional[str] = Field(None, pattern=r"^[A-Za-z]{2}$")
    language_id: Optional[str] = None
    timezone: Optional[str] = None
    notifications: Optional[bool] = None
    email_alerts: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    transaction_alerts: Optional[bool] = None
    currency: Optional[str] = None
    date_format: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

class ForgotPasswordRequest(BaseModel):
    email: str = Field(...)

class ResetPasswordRequest(BaseModel):
    token: str = Field(...)
    new_password: str = Field(..., min_length=8)

class TwoFactorVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)
