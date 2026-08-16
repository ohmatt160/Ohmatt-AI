from pydantic import  Field, model_validator
from typing import Optional
import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


load_dotenv()

class Settings(BaseSettings):
    # App settings
    PROJECT_NAME: str = "Ohmatt Finance AI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A personal finance API with bank integration"
    API_V1_STR: str = "/api/v1"
    ENV: str = Field(default="development", env="ENV")
    FRONTEND_URL: str = Field(default="http://localhost:5173", env="FRONTEND_URL")
    AUTO_SEED_GEO: bool = Field(default=True, env="AUTO_SEED_GEO")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key", env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret", env="JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60 * 24 * 7, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    SESSION_IDLE_TIMEOUT_MINUTES: int = Field(default=30, env="SESSION_IDLE_TIMEOUT_MINUTES")
    AUTH_COOKIE_NAME: str = Field(default="ohmatt_access_token", env="AUTH_COOKIE_NAME")
    AUTH_COOKIE_SECURE: bool = Field(default=True, env="AUTH_COOKIE_SECURE")
    AUTH_COOKIE_SAMESITE: str = Field(default="lax", env="AUTH_COOKIE_SAMESITE")
    ADMIN_EMAILS: str = Field(default="", env="ADMIN_EMAILS")
    BOOTSTRAP_ADMIN_EMAIL: Optional[str] = Field(default=None, env="BOOTSTRAP_ADMIN_EMAIL")
    BOOTSTRAP_ADMIN_PASSWORD: Optional[str] = Field(default=None, env="BOOTSTRAP_ADMIN_PASSWORD")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=5, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT_SECONDS: int = Field(default=30, env="DB_POOL_TIMEOUT_SECONDS")
    DB_POOL_RECYCLE_SECONDS: int = Field(default=1800, env="DB_POOL_RECYCLE_SECONDS")
    
    # Email settings
    SENDGRID_API_KEY: str = Field(default="", env="SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL: str = Field(default="", env="SENDGRID_FROM_EMAIL")
    SENDGRID_FROM_NAME: str = Field(default="Ohmatt", env="SENDGRID_FROM_NAME")
    SENDGRID_API_URL: str = Field(default="https://api.sendgrid.com/v3/mail/send", env="SENDGRID_API_URL")

    # Server-to-server sibling integration. These values must never be exposed
    # through Vite, Flutter, public runtime configuration, or API responses.
    OHMATTOS_ENABLED: bool = Field(default=False, env="OHMATTOS_ENABLED")
    OHMATTOS_BASE_URL: str = Field(default="", env="OHMATTOS_BASE_URL")
    OHMATTOS_APP_ID: str = Field(default="", env="OHMATTOS_APP_ID")
    OHMATTOS_API_KEY: str = Field(default="", env="OHMATTOS_API_KEY")
    OHMATTOS_CONNECT_TIMEOUT_SECONDS: float = Field(default=3.0, env="OHMATTOS_CONNECT_TIMEOUT_SECONDS")
    OHMATTOS_READ_TIMEOUT_SECONDS: float = Field(default=10.0, env="OHMATTOS_READ_TIMEOUT_SECONDS")
    OHMATTOS_OUTBOX_POLL_SECONDS: float = Field(default=5.0, env="OHMATTOS_OUTBOX_POLL_SECONDS")
    OHMATTOS_OUTBOX_BATCH_SIZE: int = Field(default=20, env="OHMATTOS_OUTBOX_BATCH_SIZE")
    OHMATTOS_CANARY_EMAILS: str = Field(default="", env="OHMATTOS_CANARY_EMAILS")
    OHMATTOS_ROLLOUT_PERCENT: int = Field(default=0, env="OHMATTOS_ROLLOUT_PERCENT")

    # Legacy SMTP settings are kept for local fallback only.
    MAIL_SERVER: str = Field(default="sandbox.smtp.mailtrap.io", env="MAIL_SERVER")
    MAIL_PORT: int = Field(default=2525, env="MAIL_PORT")
    MAIL_USERNAME: str = Field(default="", env="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(default="", env="MAIL_PASSWORD")
    MAIL_USE_TLS: bool = Field(default=True, env="MAIL_USE_TLS")
    MAIL_USE_SSL: bool = Field(default=False, env="MAIL_USE_SSL")
    EMAIL_TOKEN_EXPIRATION: int = Field(default=24 * 60 * 60, env="EMAIL_TOKEN_EXPIRATION")  # 24 hours
    PASSWORD_RESET_LINK_RESPONSE_ENABLED: bool = Field(
        default=False,
        env="PASSWORD_RESET_LINK_RESPONSE_ENABLED",
    )
    MAX_RECEIPT_UPLOAD_BYTES: int = Field(default=5 * 1024 * 1024, env="MAX_RECEIPT_UPLOAD_BYTES")
    VIRUS_SCAN_API_URL: str = Field(default="", env="VIRUS_SCAN_API_URL")
    VIRUS_SCAN_API_KEY: str = Field(default="", env="VIRUS_SCAN_API_KEY")
    
    # Plaid Configuration
    PLAID_CLIENT_ID: Optional[str] = Field(default=None, env="PLAID_CLIENT_ID")
    PLAID_SECRET: Optional[str] = Field(default=None, env="PLAID_SECRET")
    PLAID_ENV: str = Field(default="sandbox", env="PLAID_ENV")
    
    # Flutterwave Configuration (Africa)
    FLUTTERWAVE_ENABLED: bool = Field(default=False, env="FLUTTERWAVE_ENABLED")
    FLUTTERWAVE_SECRET_KEY: Optional[str] = Field(default=None, env="FLUTTERWAVE_SECRET_KEY")
    FLUTTERWAVE_PUBLIC_KEY: Optional[str] = Field(default=None, env="FLUTTERWAVE_PUBLIC_KEY")
    FLUTTERWAVE_ENCRYPTION_KEY: Optional[str] = Field(default=None, env="FLUTTERWAVE_ENCRYPTION_KEY")
    FLUTTERWAVE_BASE_URL: str = Field(default="https://api.flutterwave.com/v3", env="FLUTTERWAVE_BASE_URL")
    FLUTTERWAVE_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="FLUTTERWAVE_WEBHOOK_SECRET")
    
    # Paystack Configuration
    PAYSTACK_ENABLED: bool = Field(default=False, env="PAYSTACK_ENABLED")
    PAYSTACK_SECRET_KEY: Optional[str] = Field(default=None, env="PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY: Optional[str] = Field(default=None, env="PAYSTACK_PUBLIC_KEY")
    PAYSTACK_BASE_URL: str = Field(default="https://api.paystack.co", env="PAYSTACK_BASE_URL")
    PAYSTACK_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="PAYSTACK_WEBHOOK_SECRET")
    
    # Mono Configuration
    MONO_ENABLED: bool = Field(default=False, env="MONO_ENABLED")
    MONO_SECRET_KEY: Optional[str] = Field(default=None, env="MONO_SECRET_KEY")
    MONO_PUBLIC_KEY: Optional[str] = Field(default=None, env="MONO_PUBLIC_KEY")
    MONO_BASE_URL: str = Field(default="https://api.withmono.com", env="MONO_BASE_URL")
    MONO_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="MONO_WEBHOOK_SECRET")
    
    # TrueLayer Configuration (Europe)
    TRUELAYER_ENABLED: bool = Field(default=False, env="TRUELAYER_ENABLED")
    TRUELAYER_CLIENT_ID: Optional[str] = Field(default=None, env="TRUELAYER_CLIENT_ID")
    TRUELAYER_CLIENT_SECRET: Optional[str] = Field(default=None, env="TRUELAYER_CLIENT_SECRET")
    TRUELAYER_REDIRECT_URI: Optional[str] = Field(default=None, env="TRUELAYER_REDIRECT_URI")
    TRUELAYER_SANDBOX: bool = Field(default=True, env="TRUELAYER_SANDBOX")

    NVIDIA_API_KEY: str = Field(default="", env="NVIDIA_API_KEY")
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1", env="NVIDIA_BASE_URL")
    
    BACKEND_CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        env="BACKEND_CORS_ORIGINS"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def admin_emails(self) -> set[str]:
        emails = {
            email.strip().lower()
            for email in self.ADMIN_EMAILS.split(",")
            if email.strip()
        }
        if self.BOOTSTRAP_ADMIN_EMAIL:
            emails.add(self.BOOTSTRAP_ADMIN_EMAIL.strip().lower())
        return emails

    @property
    def ohmattos_canary_emails(self) -> set[str]:
        return {
            email.strip().lower()
            for email in self.OHMATTOS_CANARY_EMAILS.split(",")
            if email.strip()
        }

    @property
    def is_production(self) -> bool:
        return self.ENV.lower() == "production"

    @model_validator(mode="after")
    def validate_production_settings(self):
        if self.is_production:
            insecure_secret_values = {
                "your-secret-key",
                "your-jwt-secret",
                "",
            }
            if self.SECRET_KEY in insecure_secret_values:
                raise ValueError("SECRET_KEY must be set to a secure value in production")
            if self.JWT_SECRET_KEY in insecure_secret_values:
                raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError("DATABASE_URL must use PostgreSQL in production")
            if not self.cors_origins:
                raise ValueError("BACKEND_CORS_ORIGINS must include your frontend URL in production")
            if "*" in self.cors_origins:
                raise ValueError("BACKEND_CORS_ORIGINS cannot include * in production")
            if self.BOOTSTRAP_ADMIN_EMAIL and not self.BOOTSTRAP_ADMIN_PASSWORD:
                raise ValueError("BOOTSTRAP_ADMIN_PASSWORD is required when BOOTSTRAP_ADMIN_EMAIL is set")
            if self.AUTH_COOKIE_SAMESITE.lower() == "none" and not self.AUTH_COOKIE_SECURE:
                raise ValueError("AUTH_COOKIE_SECURE must be true when AUTH_COOKIE_SAMESITE=none")
            if self.DB_POOL_SIZE < 1 or self.DB_MAX_OVERFLOW < 0:
                raise ValueError("Database pool settings are invalid")
            if self.OHMATTOS_ENABLED:
                if not self.OHMATTOS_BASE_URL.startswith("https://"):
                    raise ValueError("OHMATTOS_BASE_URL must use HTTPS in production")
                if not self.OHMATTOS_APP_ID.strip():
                    raise ValueError("OHMATTOS_APP_ID is required when OhmattOS is enabled")
                if len(self.OHMATTOS_API_KEY.strip()) < 32:
                    raise ValueError("OHMATTOS_API_KEY must be a strong service key")
                if self.OHMATTOS_OUTBOX_BATCH_SIZE < 1:
                    raise ValueError("OHMATTOS_OUTBOX_BATCH_SIZE must be positive")
                if not 0 <= self.OHMATTOS_ROLLOUT_PERCENT <= 100:
                    raise ValueError("OHMATTOS_ROLLOUT_PERCENT must be between 0 and 100")
        return self
    
    class Config:
        case_sensitive = True

settings = Settings()
