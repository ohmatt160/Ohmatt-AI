from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.extensions import Base


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(5), unique=True, nullable=False, index=True)  # ISO 639-1
    name = Column(String(50), nullable=False)
    native_name = Column(String(50), nullable=False)

    # Relationships
    users = relationship("User", back_populates="language")