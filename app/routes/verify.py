# app/routes/verify.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.extensions import get_db
from app.models.user import User
from app.schemas.user import VerifyRequest
from app.utils.auth import confirm_token
from app.utils.i18n import t, user_language

router = APIRouter(prefix="/verify", tags=["verify"])


@router.post("")
async def verify_account(data: VerifyRequest, db: Session = Depends(get_db)):
    email = confirm_token(data.token)
    if not email:
        raise HTTPException(400, "Invalid or expired token")

    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_verified:
        return {"message": t("account_already_verified", lang=user_language(user))}

    user.is_verified = True
    db.commit()
    return {"message": t("account_verified", lang=user_language(user))}
