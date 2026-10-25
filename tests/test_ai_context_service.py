from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.extensions import Base
from app.models.ai_memory import AIPersonalMemory
from app.models.messages import Messages
from app.models.user import User
from app.routes.messages import _delete_ai_history
from app.services.ai_context_service import AIContextService


def _load_models():
    for module in (
        "app.models.country", "app.models.continent", "app.models.language",
        "app.models.transaction", "app.models.task", "app.models.bank_connection",
        "app.models.bank_account", "app.models.activity", "app.models.activity_log",
        "app.models.bank_provider", "app.models.bank_transaction", "app.models.blacklist",
        "app.models.session", "app.models.insight", "app.models.finance",
        "app.models.integration_outbox",
    ):
        __import__(module)


def _user(username: str) -> User:
    return User(
        username=username,
        email=f"{username}@example.test",
        password_hash="not-used-in-this-test",
    )


def test_context_is_user_scoped_and_bounded_and_clear_removes_both_roles():
    _load_models()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[User.__table__, Messages.__table__, AIPersonalMemory.__table__],
    )

    with Session(engine) as db:
        user = _user("owner")
        other_user = _user("other")
        ai_user = _user("ai_assistant")
        recipient = _user("recipient")
        db.add_all([user, other_user, ai_user, recipient])
        db.flush()

        start = datetime(2026, 1, 1)
        history = []
        for index in range(18):
            sender_id = user.id if index % 2 == 0 else ai_user.id
            receiver_id = ai_user.id if index % 2 == 0 else user.id
            message = Messages(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=f"owner conversation {index}",
                timestamp=start + timedelta(minutes=index),
            )
            db.add(message)
            history.append(message)

        db.add(Messages(
            sender_id=other_user.id,
            receiver_id=ai_user.id,
            content="private other-user conversation",
            timestamp=start + timedelta(days=1),
        ))
        db.add_all([
            AIPersonalMemory(user_id=user.id, content="owner saved preference"),
            AIPersonalMemory(user_id=other_user.id, content="other user's private memory"),
        ])
        db.flush()

        context = AIContextService().build(
            db,
            user_id=user.id,
            ai_user_id=ai_user.id,
            exclude_message_id=history[-1].id,
        )
        assert len(context["history"]) == 16
        assert all("other-user" not in item["content"] for item in context["history"])
        assert context["history"][-1]["content"] == "owner conversation 16"
        assert context["memories"] == ["owner saved preference"]

        forwarded = Messages(
            sender_id=user.id,
            receiver_id=recipient.id,
            content="forwarded assistant reply",
            forwarded_from_id=history[-2].id,
        )
        db.add(forwarded)
        db.flush()

        deleted_count = _delete_ai_history(db, user.id, ai_user.id)
        db.commit()

        assert deleted_count == 18
        assert db.query(Messages).filter(
            Messages.sender_id == user.id,
            Messages.receiver_id == ai_user.id,
        ).count() == 0
        forwarded_copy = db.query(Messages).filter(Messages.id == forwarded.id).one()
        assert forwarded_copy.forwarded_from_id is None
        assert db.query(AIPersonalMemory).filter(
            AIPersonalMemory.user_id == user.id,
        ).count() == 1


def test_context_includes_legacy_self_conversation_with_stable_roles():
    _load_models()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(
        engine,
        tables=[User.__table__, Messages.__table__, AIPersonalMemory.__table__],
    )

    with Session(engine) as db:
        user = _user("legacy_owner")
        ai_user = _user("ai_assistant")
        db.add_all([user, ai_user])
        db.flush()

        start = datetime(2025, 1, 1)
        for index, role in enumerate(("user", "assistant", "user", "assistant")):
            db.add(Messages(
                sender_id=user.id,
                receiver_id=user.id,
                content=f"legacy {role} message {index}",
                timestamp=start + timedelta(minutes=index),
            ))
        db.flush()

        context = AIContextService().build(
            db,
            user_id=user.id,
            ai_user_id=ai_user.id,
        )

        assert [item["role"] for item in context["history"]] == [
            "user", "assistant", "user", "assistant",
        ]
        assert [item["content"] for item in context["history"]] == [
            "legacy user message 0",
            "legacy assistant message 1",
            "legacy user message 2",
            "legacy assistant message 3",
        ]
