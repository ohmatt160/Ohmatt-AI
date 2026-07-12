from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings


def normalize_database_url(url: str) -> str:
    """Accept provider-style Postgres URLs while preserving Neon query options."""
    if url.startswith("postgres://"):
        return f"postgresql://{url[len('postgres://') :]}"
    return url


database_url = normalize_database_url(settings.DATABASE_URL)

# SQLite needs special handling for concurrent requests
if database_url.startswith("sqlite"):
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
        poolclass=NullPool,  # No connection pooling for SQLite
    )
else:
    engine = create_engine(
        database_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,
        pool_pre_ping=True,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
        pool_use_lifo=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
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
    import app.models.session
    import app.models.messages
    import app.models.insight
    import app.models.finance

    try:
        Base.metadata.create_all(bind=engine)
        ensure_runtime_columns()
        ensure_performance_indexes()
        print("[OK] Database tables created")
        seed_geo_records()
        bootstrap_admin_user()
    except Exception as e:
        print(f"[ERROR] Could not initialize database: {e}")
        if settings.is_production:
            raise
    finally:
        db_session.remove()


def ensure_runtime_columns():
    with engine.begin() as connection:
        if database_url.startswith("sqlite"):
            transaction_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(transactions)").fetchall()
            }
            if "user_category" not in transaction_columns:
                connection.exec_driver_sql(
                    "ALTER TABLE transactions ADD COLUMN user_category VARCHAR(100)"
                )
            task_columns = {
                row[1]
                for row in connection.exec_driver_sql("PRAGMA table_info(tasks)").fetchall()
            }
            if "user_id" not in task_columns:
                connection.exec_driver_sql("ALTER TABLE tasks ADD COLUMN user_id INTEGER")
            return

        connection.exec_driver_sql(
            "ALTER TABLE transactions ADD COLUMN IF NOT EXISTS user_category VARCHAR(100)"
        )
        connection.exec_driver_sql(
            "ALTER TABLE tasks ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)"
        )


def ensure_performance_indexes():
    """Create indexes used by authenticated hot paths on existing databases."""
    statements = [
        "CREATE INDEX IF NOT EXISTS ix_transactions_user_date ON transactions (user_id, date)",
        "CREATE INDEX IF NOT EXISTS ix_transactions_user_category_date ON transactions (user_id, category, date)",
        "CREATE INDEX IF NOT EXISTS ix_transactions_user_account_date ON transactions (user_id, account_id, date)",
        "CREATE INDEX IF NOT EXISTS ix_messages_receiver_read_time ON messages (receiver_id, is_read, timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_messages_sender_time ON messages (sender_id, timestamp)",
        "CREATE INDEX IF NOT EXISTS ix_insights_user_created ON insights (user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_insights_user_read_created ON insights (user_id, is_read, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_activity_logs_user_created ON activity_logs (user_id, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_activity_logs_action_created ON activity_logs (action, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_bank_accounts_user_active ON bank_account (user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_bank_accounts_connection ON bank_account (connection_id)",
        "CREATE INDEX IF NOT EXISTS ix_bank_connections_user_active ON bank_connections (user_id, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_bank_providers_api_name ON bank_providers (api_name)",
        "CREATE INDEX IF NOT EXISTS ix_bank_transactions_user_date ON bank_transaction (user_id, date)",
        "CREATE INDEX IF NOT EXISTS ix_bank_transactions_account_date ON bank_transaction (bank_account_id, date)",
        "CREATE INDEX IF NOT EXISTS ix_user_sessions_user_active_seen ON user_sessions (user_id, is_active, last_seen_at)",
        "CREATE INDEX IF NOT EXISTS ix_tasks_user_date ON tasks (user_id, date)",
        "CREATE INDEX IF NOT EXISTS ix_budgets_user_month ON budgets (user_id, month)",
        "CREATE INDEX IF NOT EXISTS ix_recurring_user_active_date ON recurring_transactions (user_id, is_active, next_date)",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.exec_driver_sql(statement)


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
