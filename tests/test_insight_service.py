from datetime import datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.services.insight_service import InsightService


for module in (
    "app.models.user", "app.models.country", "app.models.continent",
    "app.models.language", "app.models.task", "app.models.bank_connection",
    "app.models.bank_account", "app.models.activity", "app.models.activity_log",
    "app.models.bank_provider", "app.models.bank_transaction", "app.models.blacklist",
    "app.models.session", "app.models.messages", "app.models.insight",
    "app.models.finance", "app.models.transaction", "app.models.integration_outbox",
):
    __import__(module)


def make_db():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
        connection.execute(text("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, date DATETIME,
                amount FLOAT, category VARCHAR(100), user_category VARCHAR(100)
            )
        """))
        connection.execute(text("""
            CREATE TABLE insights (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, type VARCHAR(50),
                title VARCHAR(200), description TEXT, category VARCHAR(100),
                amount FLOAT, related_transaction_id INTEGER, severity VARCHAR(20), is_read BOOLEAN,
                created_at DATETIME
            )
        """))
        connection.execute(text("INSERT INTO users (id) VALUES (1)"))
    return engine


def test_insights_compare_current_month_and_use_positive_expense_sign():
    engine = make_db()
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_start = (month_start - timedelta(days=1)).replace(day=1)
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO transactions (user_id, date, amount, category)
            VALUES (1, :date, 120, 'Food')
        """), {"date": now})
        connection.execute(text("""
            INSERT INTO transactions (user_id, date, amount, category)
            VALUES (1, :date, 50, 'Food')
        """), {"date": previous_start + timedelta(days=min(now.day - 1, 1))})

    with Session(engine) as db:
        insights = InsightService.generate_insights(
            db,
            SimpleNamespace(id=1, preferences={"currency": "USD"}),
        )

    assert any(item["title"] == "Month-to-date spending is up" for item in insights)
    assert "120" in next(item["description"] for item in insights if item["title"] == "Month-to-date spending is up")
    engine.dispose()
