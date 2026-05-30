from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# SQLite needs special handling for concurrent requests
if "sqlite" in settings.DATABASE_URL:
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # No connection pooling for SQLite
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_extensions(app=None):
    import app.models.user
    import app.models.country
    import app.models.continent
    import app.models.language
    import app.models.transaction
    import app.models.task
    import app.models.bank_connection
    import app.models.bank_account
    import app.models.activity
    import app.models.bank_provider
    import app.models.bank_transaction
    import app.models.blacklist
    import app.models.messages
    import app.models.insight

    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created")
    except Exception as e:
        print(f"[WARNING] Could not create all tables: {e}")
