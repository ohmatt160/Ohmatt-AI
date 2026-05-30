# app/routes/verify.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.extensions import db_session
from app.models.user import User
from app.schemas.user import VerifyRequest
from app.utils.auth import confirm_token

router = APIRouter(prefix="/verify", tags=["verify"])


@router.post("")
async def verify_account(data: VerifyRequest):
    email = confirm_token(data.token)
    if not email:
        raise HTTPException(400, "Invalid or expired token")

    user = db_session.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(404, "User not found")
    if user.is_verified:
        return {"message": "Account already verified"}

    user.is_verified = True
    db_session.commit()
    return {"message": "Account verified successfully"}