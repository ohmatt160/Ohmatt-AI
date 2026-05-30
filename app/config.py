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
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key", env="SECRET_KEY")
    JWT_SECRET_KEY: str = Field(default="your-jwt-secret", env="JWT_SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./test.db", env="DATABASE_URL")
    
    # Email settings (for development)
    MAIL_SERVER: str = Field(default="sandbox.smtp.mailtrap.io", env="MAIL_SERVER")
    MAIL_PORT: int = Field(default=2525, env="MAIL_PORT")
    MAIL_USERNAME: str = Field(default="", env="MAIL_USERNAME")
    MAIL_PASSWORD: str = Field(default="", env="MAIL_PASSWORD")
    MAIL_USE_TLS: bool = Field(default=True, env="MAIL_USE_TLS")
    MAIL_USE_SSL: bool = Field(default=False, env="MAIL_USE_SSL")
    EMAIL_TOKEN_EXPIRATION: int = Field(default=24 * 60 * 60, env="EMAIL_TOKEN_EXPIRATION")  # 24 hours
    
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
    
    # Paystack Configuration (Nigeria/Ghana)
    PAYSTACK_ENABLED: bool = Field(default=False, env="PAYSTACK_ENABLED")
    PAYSTACK_SECRET_KEY: Optional[str] = Field(default=None, env="PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY: Optional[str] = Field(default=None, env="PAYSTACK_PUBLIC_KEY")
    PAYSTACK_BASE_URL: str = Field(default="https://api.paystack.co", env="PAYSTACK_BASE_URL")
    PAYSTACK_WEBHOOK_SECRET: Optional[str] = Field(default=None, env="PAYSTACK_WEBHOOK_SECRET")
    
    # Mono Configuration (Nigeria)
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
            if not self.cors_origins:
                raise ValueError("BACKEND_CORS_ORIGINS must include your frontend URL in production")
        return self
    
    class Config:
        case_sensitive = True

settings = Settings()
