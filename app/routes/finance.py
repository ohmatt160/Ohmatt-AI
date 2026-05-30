import csv
import io
import json
import os
import re
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.config import settings
from app.extensions import get_db
from app.models.bank_account import BankAccount
from app.models.finance import Budget, RecurringTransaction, TransactionCategory, TransactionReceipt
from app.models.insight import Insight
from app.models.messages import Messages
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.bank import CategoryPayload, BudgetPayload, RecurringPayload, OnboardingPayload, PushPayload
from app.utils.auth import get_current_user

router = APIRouter(tags=["finance"])

DEFAULT_CATEGORIES = [
    ("Food", "#10B981"),
    ("Transport", "#06B6D4"),
    ("Housing", "#8B5CF6"),
    ("Utilities", "#F59E0B"),
    ("Entertainment", "#EF4444"),
    ("Income", "#22C55E"),
    ("Uncategorized", "#8A8F98"),
]



def normalize_category_name(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip())


def serialize_transaction(t: Transaction) -> dict:
    return {
        "id": t.id,
        "description": t.description,
        "amount": t.amount,
        "date": t.date.isoformat() if t.date else None,
        "category": t.category,
        "currency": t.currency or "USD",
        "pending": bool(t.pending),
        "merchant_name": t.merchant_name,
    }


def get_month_bounds(month: str) -> tuple[datetime, datetime]:
    start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1)
    else:
        end = datetime(start.year, start.month + 1, 1)
    return start, end


def make_simple_pdf(lines: list[str]) -> bytes:
    escaped_lines = [
        line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:110]
        for line in lines[:55]
    ]
    content = "BT /F1 10 Tf 40 750 Td 14 TL " + " Tj T* ".join(f"({line})" for line in escaped_lines) + " Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        f"<< /Length {len(content.encode('latin-1', errors='ignore'))} >>\nstream\n{content}\nendstream".encode("latin-1", errors="ignore"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer << /Root 1 0 R /Size {len(objects) + 1} >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    )
    return bytes(pdf)


def ensure_default_categories(db: Session, user_id: int):
    existing = {
        category.name.lower()
        for category in db.query(TransactionCategory).filter_by(user_id=user_id).all()
    }
    for name, color in DEFAULT_CATEGORIES:
        if name.lower() not in existing:
            db.add(TransactionCategory(user_id=user_id, name=name, color=color))
    db.commit()


@router.get("/transactions/export.csv")
def export_transactions_csv(
    days: int = Query(365, ge=1, le=3650),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_date = datetime.utcnow() - timedelta(days=days)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id, Transaction.date >= start_date)
        .order_by(Transaction.date.desc())
        .all()
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "date", "description", "merchant", "category", "amount", "currency", "pending"])
    for t in transactions:
        writer.writerow([
            t.id,
            t.date.isoformat() if t.date else "",
            t.description or "",
            t.merchant_name or "",
            t.category or "",
            t.amount,
            t.currency or "USD",
            bool(t.pending),
        ])

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="transactions.csv"'},
    )


@router.get("/transactions/export.pdf")
def export_transactions_pdf(
    days: int = Query(365, ge=1, le=3650),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start_date = datetime.utcnow() - timedelta(days=days)
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id, Transaction.date >= start_date)
        .order_by(Transaction.date.desc())
        .all()
    )
    lines = [
        "Ohmatt Transaction Export",
        f"Generated: {datetime.utcnow().isoformat()} UTC",
        "",
    ]
    for t in transactions:
        lines.append(
            f"{t.date.date() if t.date else ''} | {t.description or ''} | "
            f"{t.category or 'Uncategorized'} | {t.currency or 'USD'} {t.amount:.2f}"
        )

    return Response(
        content=make_simple_pdf(lines),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="transactions.pdf"'},
    )


@router.get("/transactions/custom-categories")
def list_custom_categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_default_categories(db, current_user.id)
    categories = db.query(TransactionCategory).filter_by(user_id=current_user.id).order_by(TransactionCategory.name).all()
    return [{"id": c.id, "name": c.name, "color": c.color} for c in categories]


@router.post("/transactions/custom-categories")
def create_custom_category(payload: CategoryPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = normalize_category_name(payload.name)
    existing = db.query(TransactionCategory).filter(
        TransactionCategory.user_id == current_user.id,
        func.lower(TransactionCategory.name) == name.lower(),
    ).first()
    if existing:
        raise HTTPException(409, "Category already exists")
    category = TransactionCategory(user_id=current_user.id, name=name, color=payload.color)
    db.add(category)
    db.commit()
    db.refresh(category)
    return {"id": category.id, "name": category.name, "color": category.color}


@router.put("/transactions/custom-categories/{category_id}")
def update_custom_category(category_id: int, payload: CategoryPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    category = db.query(TransactionCategory).filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    old_name = category.name
    category.name = normalize_category_name(payload.name)
    category.color = payload.color
    db.query(Transaction).filter_by(user_id=current_user.id, category=old_name).update({"category": category.name})
    db.commit()
    return {"id": category.id, "name": category.name, "color": category.color}


@router.delete("/transactions/custom-categories/{category_id}")
def delete_custom_category(category_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    category = db.query(TransactionCategory).filter_by(id=category_id, user_id=current_user.id).first()
    if not category:
        raise HTTPException(404, "Category not found")
    db.query(Transaction).filter_by(user_id=current_user.id, category=category.name).update({"category": "Uncategorized"})
    db.delete(category)
    db.commit()
    return {"message": "Category deleted"}


@router.post("/transactions/{transaction_id}/receipt")
async def upload_receipt(transaction_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transaction = db.query(Transaction).filter_by(id=transaction_id, user_id=current_user.id).first()
    if not transaction:
        raise HTTPException(404, "Transaction not found")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "application/pdf"}:
        raise HTTPException(400, "Receipt must be an image or PDF")

    upload_dir = os.path.join(os.getcwd(), "uploads", "receipts", str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)
    extension = os.path.splitext(file.filename or "")[1] or ".bin"
    filename = f"{uuid.uuid4().hex}{extension}"
    path = os.path.join(upload_dir, filename)
    contents = await file.read()
    with open(path, "wb") as handle:
        handle.write(contents)

    receipt = TransactionReceipt(
        transaction_id=transaction.id,
        user_id=current_user.id,
        filename=file.filename or filename,
        content_type=file.content_type or "application/octet-stream",
        storage_path=path,
    )
    db.add(receipt)
    db.commit()
    db.refresh(receipt)
    return {"id": receipt.id, "filename": receipt.filename, "content_type": receipt.content_type}


@router.get("/budgets")
def list_budgets(month: Optional[str] = Query(None), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    month = month or datetime.utcnow().strftime("%Y-%m")
    start, end = get_month_bounds(month)
    budgets = db.query(Budget).filter_by(user_id=current_user.id, month=month).all()
    spending_rows = (
        db.query(Transaction.category, func.sum(Transaction.amount))
        .filter(Transaction.user_id == current_user.id, Transaction.date >= start, Transaction.date < end, Transaction.amount > 0)
        .group_by(Transaction.category)
        .all()
    )
    actuals = {category or "Uncategorized": float(total or 0) for category, total in spending_rows}
    return [
        {
            "id": b.id,
            "category": b.category,
            "month": b.month,
            "amount": b.amount,
            "actual": round(actuals.get(b.category, 0), 2),
            "remaining": round(b.amount - actuals.get(b.category, 0), 2),
            "percent_used": round((actuals.get(b.category, 0) / b.amount) * 100, 1) if b.amount else 0,
            "alert": actuals.get(b.category, 0) >= b.amount * b.alert_threshold,
            "alert_threshold": b.alert_threshold,
        }
        for b in budgets
    ]


@router.post("/budgets")
def upsert_budget(payload: BudgetPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    budget = db.query(Budget).filter_by(user_id=current_user.id, month=payload.month, category=payload.category).first()
    if not budget:
        budget = Budget(user_id=current_user.id, category=payload.category, month=payload.month)
        db.add(budget)
    budget.amount = payload.amount
    budget.alert_threshold = payload.alert_threshold
    db.commit()
    db.refresh(budget)
    return {"id": budget.id, "category": budget.category, "month": budget.month, "amount": budget.amount, "alert_threshold": budget.alert_threshold}


@router.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    budget = db.query(Budget).filter_by(id=budget_id, user_id=current_user.id).first()
    if not budget:
        raise HTTPException(404, "Budget not found")
    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted"}


@router.get("/recurring-transactions")
def list_recurring(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(RecurringTransaction).filter_by(user_id=current_user.id).order_by(RecurringTransaction.next_date).all()
    return [
        {
            "id": item.id,
            "description": item.description,
            "amount": item.amount,
            "category": item.category,
            "frequency": item.frequency,
            "next_date": item.next_date.isoformat(),
            "is_active": item.is_active,
        }
        for item in items
    ]


@router.post("/recurring-transactions")
def create_recurring(payload: RecurringPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        next_date = datetime.fromisoformat(payload.next_date)
    except ValueError:
        raise HTTPException(400, "Invalid next_date")
    item = RecurringTransaction(user_id=current_user.id, next_date=next_date, **payload.dict(exclude={"next_date"}))
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "message": "Recurring transaction created"}


@router.delete("/recurring-transactions/{item_id}")
def delete_recurring(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(RecurringTransaction).filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        raise HTTPException(404, "Recurring transaction not found")
    db.delete(item)
    db.commit()
    return {"message": "Recurring transaction deleted"}


@router.get("/dashboard/metrics")
def dashboard_metrics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.query(BankAccount).filter_by(user_id=current_user.id).all()
    total_balance = sum(float(a.balance_current or a.balance_available or 0) for a in accounts)
    now = datetime.utcnow()
    start_this_month = datetime(now.year, now.month, 1)
    start_last_month = datetime(now.year - 1, 12, 1) if now.month == 1 else datetime(now.year, now.month - 1, 1)
    txs = db.query(Transaction).filter(Transaction.user_id == current_user.id, Transaction.date >= start_last_month).all()

    monthly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    weekly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for tx in txs:
        key = tx.date.strftime("%Y-%m") if tx.date else now.strftime("%Y-%m")
        week = tx.date.strftime("%Y-W%U") if tx.date else now.strftime("%Y-W%U")
        amount = float(tx.amount or 0)
        bucket = "income" if amount < 0 else "expense"
        monthly[key][bucket] += abs(amount)
        weekly[week][bucket] += abs(amount)

    return {
        "total_balance": round(total_balance, 2),
        "net_worth": round(total_balance, 2),
        "monthly": [{"period": k, **v} for k, v in sorted(monthly.items())],
        "weekly": [{"period": k, **v} for k, v in sorted(weekly.items())],
        "this_month": monthly[start_this_month.strftime("%Y-%m")],
        "last_month": monthly[start_last_month.strftime("%Y-%m")],
    }


@router.get("/data/export")
def export_user_data(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    payload = {
        "user": {"id": current_user.id, "username": current_user.username, "email": current_user.email, "preferences": current_user.preferences},
        "transactions": [serialize_transaction(t) for t in db.query(Transaction).filter_by(user_id=current_user.id).all()],
        "budgets": [
            {
                "id": b.id,
                "category": b.category,
                "month": b.month,
                "amount": b.amount,
                "alert_threshold": b.alert_threshold,
            }
            for b in db.query(Budget).filter_by(user_id=current_user.id).all()
        ],
        "categories": [{"name": c.name, "color": c.color} for c in db.query(TransactionCategory).filter_by(user_id=current_user.id).all()],
        "messages": [
            {"id": m.id, "sender_id": m.sender_id, "receiver_id": m.receiver_id, "content": m.content, "timestamp": m.timestamp.isoformat() if m.timestamp else None}
            for m in db.query(Messages).filter((Messages.sender_id == current_user.id) | (Messages.receiver_id == current_user.id)).all()
        ],
        "insights": [
            {"id": i.id, "title": i.title, "description": i.description, "created_at": i.created_at.isoformat() if i.created_at else None}
            for i in db.query(Insight).filter_by(user_id=current_user.id).all()
        ],
    }
    return Response(
        content=json.dumps(payload, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="ohmatt-data-export.json"'},
    )


@router.post("/onboarding")
def set_onboarding(payload: OnboardingPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = dict(current_user.preferences or {})
    preferences["onboarding_completed"] = payload.completed
    current_user.preferences = preferences
    db.commit()
    return {"onboarding_completed": payload.completed}


@router.post("/notifications/push")
def set_push_notifications(payload: PushPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    preferences = dict(current_user.preferences or {})
    preferences["push_notifications"] = payload.enabled
    preferences["notifications"] = payload.enabled
    current_user.preferences = preferences
    db.commit()
    return {"push_notifications": payload.enabled}
