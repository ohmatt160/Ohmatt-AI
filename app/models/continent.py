from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.extensions import Base


class Continent(Base):
    __tablename__ = "continents"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(2), unique=True, nullable=False, index=True)  # AF, AS, EU, NA, SA, OC, AN
    name = Column(String(50), nullable=False)

    # Relationships
    users = relationship("User", back_populates="continent")