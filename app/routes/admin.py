from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.extensions import get_db
from app.config import settings
from app.models.bank_account import BankAccount
from app.models.bank_connection import BankConnection
from app.models.bank_provider import BankProvider
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.user import UserResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def admin_required(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    return current_user



@router.get("/stats")
async def get_stats(
        admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """Get system statistics"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = sum(
        1
        for (preferences,) in db.query(User.preferences).yield_per(500)
        if (preferences or {}).get("is_active", True)
    )
    admin_users = db.query(func.count(User.id)).filter(User.is_admin == True).scalar() or 0
    verified_users = db.query(func.count(User.id)).filter(User.is_verified == True).scalar() or 0
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    pending_transactions = db.query(func.count(Transaction.id)).filter(Transaction.pending == True).scalar() or 0
    total_accounts = db.query(func.count(BankAccount.id)).scalar() or 0
    active_accounts = db.query(func.count(BankAccount.id)).filter(BankAccount.is_active == True).scalar() or 0
    total_connections = db.query(func.count(BankConnection.id)).scalar() or 0
    active_connections = db.query(func.count(BankConnection.id)).filter(BankConnection.is_active == True).scalar() or 0
    active_providers = db.query(func.count(BankProvider.id)).filter(BankProvider.is_active == True).scalar() or 0

    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "admins": admin_users,
            "verified": verified_users,
        },
        "transactions": {
            "total": total_transactions,
            "pending": pending_transactions,
        },
        "accounts": {
            "total": total_accounts,
            "active": active_accounts,
        },
        "connections": {
            "total": total_connections,
            "active": active_connections,
        },
        "providers": {
            "active": active_providers,
        },
        "system": {
            "version": settings.VERSION,
            "environment": "development" if "sqlite" in settings.DATABASE_URL else "configured",
            "database": settings.DATABASE_URL.split(":", 1)[0],
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/users", response_model=List[UserResponse])
async def list_users(
        search: Optional[str] = Query(None, max_length=100),
        admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    query = db.query(User)
    if search:
        query = query.filter(
            User.username.ilike(f"%{search}%") | User.email.ilike(f"%{search}%")
        )

    users = query.order_by(User.id.desc()).limit(100).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_admin": u.is_admin,
            "is_verified": u.is_verified,
            "is_active": (u.preferences or {}).get("is_active", True),
            "country_id": str(u.country_id) if u.country_id is not None else None,
            "timezone": u.timezone,
            "currency": (u.preferences or {}).get("currency", "USD"),
            "created_at": None,
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
async def update_role(
        user_id: int,
        role: str = Query(..., pattern="^(admin|user)$"),
        admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """Update user role (admin only)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot change your own role")

    user.is_admin = (role == "admin")
    db.commit()
    return {"message": f"User {user.username} is now {'admin' if user.is_admin else 'user'}"}


@router.delete("/users/{user_id}")
async def delete_user(
        user_id: int,
        admin: User = Depends(admin_required),
        db: Session = Depends(get_db)
):
    """Deactivate a user (admin only)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == admin.id:
        raise HTTPException(400, "Cannot delete yourself")

    preferences = dict(user.preferences or {})
    preferences["is_active"] = False
    user.preferences = preferences
    db.commit()
    return {"message": f"User {user.username} deactivated"}
