from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import relationship
from app.extensions import Base


class BankProvider(Base):
    __tablename__ = "bank_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    api_name = Column(String(50), nullable=False, index=True)  # plaid, flutterwave, etc.
    country_codes = Column(String(500))  # Comma-separated country codes
    continent_codes = Column(String(100))  # Comma-separated continent codes
    is_active = Column(Boolean, default=True)
    api_config = Column(JSON)  # Store provider-specific config

    # Relationships
    connections = relationship("BankConnection", back_populates="provider")
