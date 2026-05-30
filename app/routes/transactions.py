# app/routes/transactions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta


from app.extensions import get_db, db_session
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.transactions import TransactionCreate, TransactionResponse
from app.services.ai_service import ai_service
from app.utils.auth import get_current_user
# Add this after transaction is saved
from app.services.insight_service import InsightService
from app.models.insight import Insight


router = APIRouter(prefix="/transactions", tags=["transactions"])




@router.post("", response_model=dict)
async def create_transaction(
    data: TransactionCreate,
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

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    InsightService.generate_insights(db_session, current_user)

    # Get insights
    recent_transactions = (
        db_session.query(Transaction)
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.date.desc())
        .limit(20)
        .all()
    )
    insights = ai_service.analyze_spending(recent_transactions)


    return {
        "message": "Transaction added successfully",
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

    query = db_session.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date
    )

    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    transactions = query.order_by(Transaction.date.desc()).all()

    return [
        {
            "id": t.id,
            "description": t.description,
            "amount": t.amount,
            "date": t.date.isoformat() if t.date else None,
            "category": t.category,
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
    transactions = (
        db_session.query(Transaction)
        .filter_by(user_id=current_user.id)
        .all()
    )

    categories = {}
    for t in transactions:
        cat = t.category or "Uncategorized"
        if cat not in categories:
            categories[cat] = {"total": 0, "count": 0}
        categories[cat]["total"] += t.amount
        categories[cat]["count"] += 1

    return {
        "categories": [
            {"name": k, "total": round(v["total"], 2), "count": v["count"]}
            for k, v in sorted(categories.items(), key=lambda x: x[1]["total"], reverse=True)
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

    insights = db_session.query(Insight).filter(
        Insight.user_id == current_user.id,
        Insight.created_at >= start_date
    ).order_by(Insight.created_at.desc()).all()

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


@router.put("/insights/{insight_id}/read")
async def mark_insight_read(
        insight_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Mark an AI insight as read"""

    insight = db_session.query(Insight).filter(
        Insight.id == insight_id,
        Insight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(404, "Insight not found")

    insight.is_read = True
    db_session.commit()

    return {"success": True}
