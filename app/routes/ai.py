from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.extensions import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/retrain")
def retrain_ai_model(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")

    # Online training from the live multi-user ledger risks cross-user data
    # leakage and produces inconsistent per-worker models. Training is disabled
    # until a reviewed, privacy-safe offline dataset/artifact pipeline exists.
    raise HTTPException(
        status_code=409,
        detail="Online model retraining is disabled until a reviewed training dataset is available.",
    )


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
