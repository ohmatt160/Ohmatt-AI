# app/routes/users.py (NEW FILE)
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.extensions import get_db
from app.models.user import User
from app.utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/search")
def search_users(
        q: str = Query(..., min_length=2),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Search users by username or email"""
    users = db.query(User).filter(
        (User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).limit(20).all()

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
        }
        for u in users if u.id != current_user.id
    ]
