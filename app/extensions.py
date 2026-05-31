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
    import app.models.activity_log
    import app.models.bank_provider
    import app.models.bank_transaction
    import app.models.blacklist
    import app.models.messages
    import app.models.insight
    import app.models.finance

    try:
        Base.metadata.create_all(bind=engine)
        ensure_runtime_columns()
        print("[OK] Database tables created")
        seed_geo_records()
        bootstrap_admin_user()
    except Exception as e:
        print(f"[WARNING] Could not create all tables: {e}")


def ensure_runtime_columns():
    if "sqlite" not in settings.DATABASE_URL:
        return

    with engine.connect() as connection:
        transaction_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(transactions)").fetchall()
        }
        if "user_category" not in transaction_columns:
            connection.exec_driver_sql("ALTER TABLE transactions ADD COLUMN user_category VARCHAR(100)")
            connection.commit()


def seed_geo_records():
    if not settings.AUTO_SEED_GEO:
        return

    from app.services.geo_seed import seed_geo_data

    result = seed_geo_data()
    print(
        "[OK] Geography data ready: "
        f"{result['totals']['countries']} countries, "
        f"{result['totals']['languages']} languages, "
        f"{result['totals']['continents']} continents"
    )


def bootstrap_admin_user():
    if not settings.BOOTSTRAP_ADMIN_EMAIL:
        return

    from app.models.user import User

    email = settings.BOOTSTRAP_ADMIN_EMAIL.strip().lower()
    username = email.split("@")[0]
    user = db_session.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            username=username,
            email=email,
            timezone="UTC",
            is_admin=True,
            is_verified=True,
            preferences={
                "currency": "USD",
                "date_format": "YYYY-MM-DD",
                "notifications": True,
                "email_alerts": True,
                "transaction_alerts": True,
                "two_factor_enabled": False,
            },
        )
        user.set_password(settings.BOOTSTRAP_ADMIN_PASSWORD)
        db_session.add(user)
        db_session.commit()
        print(f"[OK] Bootstrap admin created: {email}")
        return

    changed = False
    if not user.is_admin:
        user.is_admin = True
        changed = True
    if not user.is_verified:
        user.is_verified = True
        changed = True
    if settings.BOOTSTRAP_ADMIN_PASSWORD:
        user.set_password(settings.BOOTSTRAP_ADMIN_PASSWORD)
        changed = True
    if changed:
        db_session.commit()
        print(f"[OK] Bootstrap admin updated: {email}")
