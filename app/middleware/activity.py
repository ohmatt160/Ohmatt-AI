from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog


def log_activity(
    db: Session,
    request: Optional[Request],
    user_id: int,
    action: str,
    *,
    entity_type: str | None = None,
    entity_id: str | int | None = None,
    description: str | None = None,
    metadata: dict | None = None,
    commit: bool = True,
    **kwargs,
):
    """Log user activity"""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        description=description,
        metadata_json=metadata or kwargs.pop("metadata_json", None),
        endpoint=str(request.url.path) if request else kwargs.pop("endpoint", None),
        ip_address=request.client.host if request and request.client else kwargs.pop("ip_address", None),
        user_agent=request.headers.get("user-agent") if request else kwargs.pop("user_agent", None),
        **kwargs
    )
    db.add(log)
    if commit:
        db.commit()
    else:
        db.flush()
    return log
