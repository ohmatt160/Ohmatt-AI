from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.middleware.activity import log_activity
from app.models.transaction import Transaction
from app.models.user import User
from app.services.ai_service import ai_service
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/retrain")
def retrain_ai_model(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")

    corrected = (
        db.query(Transaction)
        .filter(Transaction.user_category.isnot(None))
        .all()
    )
    trained_samples = ai_service.retrain_from_corrections(corrected)

    log_activity(db,
        request,
        current_user.id,
        "ai_retrain",
        entity_type="ai_model",
        description=f"AI retrained with {trained_samples} corrected samples",
        metadata={"corrected_samples": trained_samples, "trained_at": datetime.utcnow().isoformat()},
    )

    return {
        "message": "AI retraining completed",
        "corrected_samples": trained_samples,
        "status": "completed",
    }


@router.get("/accuracy")
def get_ai_accuracy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")

    total_categorized = db.query(Transaction).filter(Transaction.category.isnot(None)).count()
    corrected = db.query(Transaction).filter(Transaction.user_category.isnot(None)).count()
    matching_corrections = (
        db.query(Transaction)
        .filter(
            Transaction.user_category.isnot(None),
            func.lower(Transaction.user_category) == func.lower(Transaction.category),
        )
        .count()
    )
    reviewed = corrected
    accuracy = (
        round((matching_corrections / reviewed) * 100, 2)
        if reviewed
        else round(((total_categorized - corrected) / total_categorized) * 100, 2)
        if total_categorized
        else 0
    )

    return {
        "total_categorized": total_categorized,
        "corrected": corrected,
        "reviewed": reviewed,
        "matching_corrections": matching_corrections,
        "accuracy": accuracy,
    }
