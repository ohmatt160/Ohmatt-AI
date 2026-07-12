from datetime import datetime, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.services.transaction_context_service import TransactionContextService


def test_context_covers_complete_user_ledger_and_excludes_other_users():
    for module in (
        "app.models.user", "app.models.country", "app.models.continent",
        "app.models.language", "app.models.task", "app.models.bank_connection",
        "app.models.bank_account", "app.models.activity", "app.models.activity_log",
        "app.models.bank_provider", "app.models.bank_transaction", "app.models.blacklist",
        "app.models.session", "app.models.messages", "app.models.insight",
        "app.models.finance",
    ):
        __import__(module)

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date DATETIME,
                description VARCHAR(500),
                amount FLOAT,
                category VARCHAR(100),
                user_category VARCHAR(100)
            )
        """))
        start = datetime(2025, 1, 1)
        for index in range(75):
            connection.execute(
                text("""
                    INSERT INTO transactions
                        (id, user_id, date, description, amount, category, user_category)
                    VALUES
                        (:id, 1, :date, :description, 10, 'Food', NULL)
                """),
                {
                    "id": index + 1,
                    "date": start + timedelta(days=index),
                    "description": "HiddenMerchant" if index == 30 else f"Purchase {index}",
                },
            )
        connection.execute(text("""
            INSERT INTO transactions
                (id, user_id, date, description, amount, category, user_category)
            VALUES
                (1000, 2, '2025-01-01', 'Other User Secret', 99999, 'Private', NULL)
        """))

    with Session(engine) as db:
        context = TransactionContextService.build(
            db,
            user_id=1,
            currency="USD",
            message="What did I pay HiddenMerchant?",
        )

    assert "all 75 transactions" in context
    assert "Food: 75 transactions" in context
    assert "HiddenMerchant" in context
    assert "Other User Secret" not in context
    assert "99999" not in context
