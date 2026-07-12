from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi import Request
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from datetime import datetime, timedelta
from app.extensions import get_db, db_session
from app.models.activity_log import ActivityLog
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/activity", tags=["activity"])


class FeedbackCreate(BaseModel):
    feedback_type: str = Field(..., pattern="^(bug|feature_request|general)$")
    description: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)


def serialize_activity(log: ActivityLog):
    return {
        "id": log.id,
        "user_id": log.user_id,
        "username": log.user.username if log.user else None,
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "description": log.description,
        "metadata": log.metadata_json,
        "endpoint": log.endpoint,
        "ip_address": log.ip_address,
        "feedback_type": log.feedback_type,
        "rating": log.feedback_rating,
        "status": log.feedback_status,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/logs")
async def get_activity_logs(
        action: Optional[str] = Query(None),
        user_id: Optional[int] = Query(None),
        search: Optional[str] = Query(None),
        days: int = Query(7),
        limit: int = Query(100),
        offset: int = Query(0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get activity logs (admin sees all, users see their own)"""
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(ActivityLog).options(joinedload(ActivityLog.user)).join(User).filter(
        ActivityLog.created_at >= start_date
    )

    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)
    elif user_id:
        query = query.filter_by(user_id=user_id)

    if action:
        query = query.filter_by(action=action)
    if search and current_user.is_admin:
        like = f"%{search}%"
        query = query.filter((User.username.ilike(like)) | (User.email.ilike(like)))

    logs = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()

    return [serialize_activity(log) for log in logs]


@router.get("/user/{user_id}")
async def get_user_activity_history(
        user_id: int,
        action: Optional[str] = Query(None),
        days: int = Query(90),
        limit: int = Query(100),
        offset: int = Query(0),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(403, "Not authorized")
    query = db.query(ActivityLog).options(joinedload(ActivityLog.user)).filter(
        ActivityLog.user_id == user_id,
        ActivityLog.created_at >= datetime.utcnow() - timedelta(days=days),
    )
    if action:
        query = query.filter_by(action=action)
    logs = query.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()
    return [serialize_activity(log) for log in logs]


@router.get("/trends")
async def get_activity_trends(
        period: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
        days: int = Query(30, ge=1, le=365),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")

    rows = (
        db.query(ActivityLog.created_at, ActivityLog.action)
        .filter(ActivityLog.created_at >= datetime.utcnow() - timedelta(days=days))
        .all()
    )
    buckets: dict[str, dict[str, int]] = {}
    for created_at, action in rows:
        if period == "monthly":
            key = created_at.strftime("%Y-%m")
        elif period == "weekly":
            key = created_at.strftime("%Y-W%U")
        else:
            key = created_at.strftime("%Y-%m-%d")
        if key not in buckets:
            buckets[key] = {"period": key, "count": 0}
        buckets[key]["count"] += 1
        buckets[key][action] = buckets[key].get(action, 0) + 1
    return [buckets[key] for key in sorted(buckets)]


@router.post("/feedback")
async def submit_feedback(
        payload: FeedbackCreate,
        current_user: User = Depends(get_current_user),
        request: Request = None,
        db: Session = Depends(get_db),
):
    """Submit feedback or report a bug"""
    feedback = ActivityLog(
        user_id=current_user.id,
        action="feedback",
        feedback_type=payload.feedback_type,
        feedback_rating=payload.rating,
        description=payload.description,
        feedback_status="new",
        ip_address=request.client.host if request else None,
        endpoint=str(request.url.path) if request else None,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {"message": "Feedback submitted. Thank you!", "id": feedback.id}


@router.get("/feedback")
async def get_feedback(
        status: Optional[str] = Query(None),
        feedback_type: Optional[str] = Query(None),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get feedback (admin sees all, users see their own)"""
    query = db.query(ActivityLog).options(joinedload(ActivityLog.user)).filter(
        ActivityLog.action == "feedback"
    )

    if not current_user.is_admin:
        query = query.filter_by(user_id=current_user.id)

    if status:
        query = query.filter_by(feedback_status=status)
    if feedback_type:
        query = query.filter_by(feedback_type=feedback_type)

    feedbacks = query.order_by(ActivityLog.created_at.desc()).limit(100).all()

    return [serialize_activity(f) for f in feedbacks]


@router.get("/feedback/stats")
async def get_feedback_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    base = db.query(ActivityLog).filter(ActivityLog.action == "feedback")
    by_type = dict(base.with_entities(ActivityLog.feedback_type, func.count(ActivityLog.id)).group_by(ActivityLog.feedback_type).all())
    by_status = dict(base.with_entities(ActivityLog.feedback_status, func.count(ActivityLog.id)).group_by(ActivityLog.feedback_status).all())
    avg_rating = base.with_entities(func.avg(ActivityLog.feedback_rating)).scalar() or 0
    pending = base.filter(ActivityLog.feedback_status == "new").count()
    return {
        "total": base.count(),
        "pending": pending,
        "average_rating": round(float(avg_rating), 2),
        "by_type": by_type,
        "by_status": by_status,
    }


@router.get("/stats")
async def get_activity_stats(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    today = datetime.utcnow().date()
    start_today = datetime(today.year, today.month, today.day)
    actions_today = db.query(ActivityLog).filter(ActivityLog.created_at >= start_today).count()
    pending_feedback = db.query(ActivityLog).filter_by(action="feedback", feedback_status="new").count()
    top_actions = (
        db.query(ActivityLog.action, func.count(ActivityLog.id).label("count"))
        .group_by(ActivityLog.action)
        .order_by(func.count(ActivityLog.id).desc())
        .limit(5)
        .all()
    )
    return {
        "actions_today": actions_today,
        "pending_feedback": pending_feedback,
        "top_actions": [{"action": action, "count": count} for action, count in top_actions],
    }


@router.put("/feedback/{feedback_id}")
async def update_feedback_status(
        feedback_id: int,
        status: str = Query(..., pattern="^(new|reviewed|resolved)$"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Admin: Update feedback status"""
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")

    feedback = db.get(ActivityLog, feedback_id)
    if not feedback:
        raise HTTPException(404, "Feedback not found")

    feedback.feedback_status = status
    db.commit()
    return {"message": f"Feedback marked as {status}"}
