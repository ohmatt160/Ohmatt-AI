from sqlalchemy import Column, Integer, String, ForeignKey
from app.extensions import Base


class Blacklist(Base):
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(120), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)