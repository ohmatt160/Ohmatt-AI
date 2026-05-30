import bcrypt
from sqlalchemy import Column, Integer, String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.extensions import Base


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)  # renamed for clarity
    db_name = Column(String(100), unique=True)

    country_id = Column(Integer, ForeignKey('countries.id'))
    continent_id = Column(Integer, ForeignKey('continents.id'))
    language_id = Column(Integer, ForeignKey('languages.id'))
    timezone = Column(String(50), default='UTC')

    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    preferences = Column(JSON, default=lambda: {
        'currency': 'USD',
        'date_format': 'YYYY-MM-DD',
        'notifications': True
    })

    # Relationships
    country = relationship("Country", back_populates="users")
    continent = relationship("Continent", back_populates="users")
    language = relationship("Language", back_populates="users")
    bank_connections = relationship("BankConnection", back_populates="user")
    activities = relationship("Activity", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    bank_accounts = relationship("BankAccount", back_populates="user")
    sent_messages = relationship("Messages", foreign_keys="Messages.sender_id", back_populates="sender")
    received_messages = relationship("Messages", foreign_keys="Messages.receiver_id", back_populates="receiver")
    user_bank_transactions = relationship("BankTransaction", back_populates="user")
    insights = relationship("Insight", back_populates="user")
    insights = relationship("Insight", back_populates="user")

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def check_password(self, password):
        return verify_password(password, self.password_hash)
