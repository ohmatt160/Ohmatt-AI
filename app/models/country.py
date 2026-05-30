from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.extensions import Base


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(2), unique=True, nullable=False, index=True)  # ISO 3166-1 alpha-2
    name = Column(String(100), nullable=False)
    continent = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)  # ISO 4217
    timezone = Column(String(50), nullable=False)
    language = Column(String(5), nullable=False)  # ISO 639-1
    plaid_supported = Column(Boolean, default=False)
    plaid_country_code = Column(String(2))  # Plaid's country code
    other_provider = Column(String(50))  # Alternative provider name

    # Relationships
    users = relationship("User", back_populates="country")