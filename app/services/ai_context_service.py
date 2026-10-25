from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.ai_memory import AIPersonalMemory
from app.models.messages import Messages


class AIContextService:
    """Load bounded, user-owned conversational context for any AI product."""

    HISTORY_LIMIT = 16
    HISTORY_CHAR_LIMIT = 8_000
    MEMORY_LIMIT = 20
    MEMORY_CHAR_LIMIT = 5_000

    def build(
        self,
        db: Session,
        *,
        user_id: int,
        ai_user_id: int,
        exclude_message_id: int | None = None,
    ) -> dict[str, list]:
        conversation_filter = or_(
            (Messages.sender_id == user_id) & (Messages.receiver_id == ai_user_id),
            (Messages.sender_id == ai_user_id) & (Messages.receiver_id == user_id),
            (Messages.sender_id == user_id) & (Messages.receiver_id == user_id),
        )
        history_query = db.query(Messages).filter(
            conversation_filter,
            Messages.is_deleted.is_not(True),
        )
        if exclude_message_id is not None:
            history_query = history_query.filter(Messages.id != exclude_message_id)

        history_rows = (
            history_query.order_by(Messages.timestamp.desc(), Messages.id.desc())
            .limit(self.HISTORY_LIMIT)
            .all()
        )

        legacy_total = (
            db.query(func.count(Messages.id))
            .filter(
                Messages.sender_id == user_id,
                Messages.receiver_id == user_id,
                Messages.is_deleted.is_not(True),
            )
            .scalar()
            or 0
        )
        legacy_start = max(0, legacy_total - sum(
            1 for row in history_rows if row.sender_id == user_id and row.receiver_id == user_id
        ))
        history = []
        remaining_chars = self.HISTORY_CHAR_LIMIT
        legacy_index = legacy_start
        legacy_roles = {}
        for row in reversed(history_rows):
            if row.sender_id == user_id and row.receiver_id == user_id:
                legacy_roles[row.id] = "user" if legacy_index % 2 == 0 else "assistant"
                legacy_index += 1

        for row in reversed(history_rows):
            content = (row.content or "")[:remaining_chars]
            if not content:
                continue
            history.append({
                "role": legacy_roles.get(
                    row.id,
                    "assistant" if row.sender_id == ai_user_id else "user",
                ),
                "content": content,
            })
            remaining_chars -= len(content)
            if remaining_chars <= 0:
                break

        memory_rows = (
            db.query(AIPersonalMemory.content)
            .filter(AIPersonalMemory.user_id == user_id)
            .order_by(AIPersonalMemory.created_at.desc(), AIPersonalMemory.id.desc())
            .limit(self.MEMORY_LIMIT)
            .all()
        )
        memories = []
        remaining_chars = self.MEMORY_CHAR_LIMIT
        for (content,) in memory_rows:
            value = (content or "")[:remaining_chars]
            if not value:
                continue
            memories.append(value)
            remaining_chars -= len(value)
            if remaining_chars <= 0:
                break

        return {"history": history, "memories": memories}


ai_context_service = AIContextService()
