# app/routes/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta


from app.extensions import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.transactions import TransactionCreate, TransactionResponse
from app.services.ai_service import ai_service
from app.utils.auth import get_current_user
from app.utils.i18n import t, user_language
# Add this after transaction is saved
from app.services.insight_service import InsightService
from app.models.insight import Insight
from app.middleware.activity import log_activity


router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    category: Optional[str] = None


class CategoryCorrection(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)



@router.post("", response_model=dict)
async def create_transaction(
    data: TransactionCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a transaction with AI categorization"""
    # Parse date
    transaction_date = None
    if data.date:
        try:
            transaction_date = datetime.strptime(data.date, "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD HH:MM")
    else:
        transaction_date = datetime.utcnow()

    # AI categorization
    category, confidence = ai_service.categorize_transaction(data.description)

    # Create transaction
    transaction = Transaction(
        user_id=current_user.id,
        description=data.description,
        amount=data.amount,
        date=transaction_date,
        datetime=transaction_date,
        category=category,
        ml_confidence=confidence,
        currency=(current_user.preferences or {}).get("currency", "USD"),
        pending=False
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    InsightService.generate_insights(db, current_user)
    log_activity(
        request,
        current_user.id,
        "transaction_create",
        entity_type="transaction",
        entity_id=transaction.id,
        description=f"Created transaction: {transaction.description}",
        metadata={"amount": transaction.amount, "category": transaction.category},
    )
    log_activity(
        request,
        current_user.id,
        "insight_generation",
        entity_type="insight",
        description="Generated insights after transaction creation",
    )

    # Get insights
    recent_transactions = (
        db.query(Transaction)
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.date.desc())
        .limit(20)
        .all()
    )
    insights = ai_service.analyze_spending(recent_transactions)


    return {
        "message": t("transaction_added", lang=user_language(current_user)),
        "transaction": {
            "id": transaction.id,
            "description": transaction.description,
            "amount": transaction.amount,
            "date": transaction.date.isoformat() if transaction.date else None,
            "category": transaction.category,
            "confidence": transaction.ml_confidence,
        },
        "insights": insights,
    }


@router.get("", response_model=List[TransactionResponse])
async def list_transactions(
    days: int = Query(30, ge=1, le=365),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transactions with optional filtering"""
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date
    )

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    transactions = query.order_by(Transaction.date.desc()).limit(500).all()

    return [
        {
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "date": t.date.isoformat() if t.date else None,
            "category": t.category,
            "user_category": t.user_category,
            "ml_confidence": t.ml_confidence,
            "currency": t.currency or "USD",
            "pending": t.pending or False,
            "merchant_name": t.merchant_name,
        }
        for t in transactions
    ]

@router.get("/categories")
async def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's spending by category"""
    category_rows = (
        db.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        )
        .filter(Transaction.user_id == current_user.id)
        .group_by(Transaction.category)
        .all()
    )

    return {
        "categories": [
            {
                "name": category or "Uncategorized",
                "total": round(float(total or 0), 2),
                "count": count,
            }
            for category, total, count in sorted(
                category_rows,
                key=lambda row: float(row[1] or 0),
                reverse=True,
            )
        ]
    }


# app/routes/transactions.py - add
@router.get("/insights")
async def get_insights(
        days: int = Query(30),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get stored AI insights"""

    start_date = datetime.utcnow() - timedelta(days=days)

    insights = db.query(Insight).filter(
        Insight.user_id == current_user.id,
        Insight.created_at >= start_date
    ).order_by(Insight.created_at.desc()).limit(100).all()

    return [
        {
            "id": i.id,
            "type": i.type,
            "title": i.title,
            "description": i.description,
            "category": i.category,
            "amount": i.amount,
            "severity": i.severity,
            "is_read": i.is_read,
            "created_at": i.created_at.isoformat()
        }
        for i in insights
    ]


@router.put("/{transaction_id}", response_model=dict)
async def update_transaction(
        transaction_id: int,
        data: TransactionUpdate,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter_by(id=transaction_id, user_id=current_user.id).first()
    if not transaction:
        raise HTTPException(404, "Transaction not found")

    update_data = data.dict(exclude_unset=True)
    if "date" in update_data and update_data["date"]:
        try:
            update_data["date"] = datetime.strptime(update_data["date"], "%Y-%m-%d %H:%M")
            transaction.datetime = update_data["date"]
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD HH:MM")

    for field, value in update_data.items():
        setattr(transaction, field, value)

    db.commit()
    db.refresh(transaction)
    log_activity(
        request,
        current_user.id,
        "transaction_update",
        entity_type="transaction",
        entity_id=transaction.id,
        description=f"Updated transaction: {transaction.description}",
        metadata={"fields": list(update_data.keys())},
    )
    return {"message": t("transaction_updated", lang=user_language(current_user)), "transaction": {"id": transaction.id, "category": transaction.category}}


@router.delete("/{transaction_id}")
async def delete_transaction(
        transaction_id: int,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter_by(id=transaction_id, user_id=current_user.id).first()
    if not transaction:
        raise HTTPException(404, "Transaction not found")
    description = transaction.description
    db.delete(transaction)
    db.commit()
    log_activity(
        request,
        current_user.id,
        "transaction_delete",
        entity_type="transaction",
        entity_id=transaction_id,
        description=f"Deleted transaction: {description}",
    )
    return {"message": t("transaction_deleted", lang=user_language(current_user))}


@router.put("/{transaction_id}/category")
async def correct_transaction_category(
        transaction_id: int,
        data: CategoryCorrection,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter_by(id=transaction_id, user_id=current_user.id).first()
    if not transaction:
        raise HTTPException(404, "Transaction not found")
    previous = transaction.category
    transaction.user_category = data.category
    transaction.category = data.category
    db.commit()
    log_activity(
        request,
        current_user.id,
        "ai_category_correction",
        entity_type="transaction",
        entity_id=transaction.id,
        description=f"Corrected AI category from {previous or t('uncategorized', lang=user_language(current_user))} to {data.category}",
        metadata={"previous_category": previous, "corrected_category": data.category},
    )
    return {
        "message": t("category_correction_saved", lang=user_language(current_user)),
        "id": transaction.id,
        "category": transaction.category,
        "user_category": transaction.user_category,
    }


@router.put("/insights/{insight_id}/read")
async def mark_insight_read(
        insight_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Mark an AI insight as read"""

    insight = db.query(Insight).filter(
        Insight.id == insight_id,
        Insight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(404, "Insight not found")

    insight.is_read = True
    db.commit()

    return {"success": True}
