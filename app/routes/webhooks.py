# app/routes/webhooks.py
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import hashlib, hmac, json
from app.extensions import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.services.ai_service import ai_service
from app.config import settings
from app.utils.i18n import user_currency

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/flutterwave")
async def flutterwave_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive transaction notifications from Flutterwave"""
    payload = await request.json()
    signature = request.headers.get("verif-hash", "")

    expected_signature = settings.FLUTTERWAVE_WEBHOOK_SECRET
    if not expected_signature:
        raise HTTPException(503, "Webhook is not configured")
    if not signature or not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(401, "Invalid signature")

    event = payload.get("event")
    data = payload.get("data", {})

    if event == "charge.completed" and data.get("status") == "successful":
        # Find user by customer email
        customer = data.get("customer", {})
        email = customer.get("email")
        if email:
            user = db.query(User).filter_by(email=email).first()
            if user:
                transaction_id = str(data.get("id")) if data.get("id") is not None else None
                if transaction_id and db.query(Transaction.id).filter_by(transaction_id=transaction_id).first():
                    return {"status": "ok"}
                description = data.get("narration", "Flutterwave payment")
                amount = data.get("amount", 0)
                category, confidence = ai_service.categorize_transaction(description)

                transaction = Transaction(
                    user_id=user.id,
                    description=description,
                    amount=amount,
                    date=datetime.utcnow(),
                    datetime=datetime.utcnow(),
                    category=category,
                    ml_confidence=confidence,
                    transaction_id=transaction_id,
                    currency=data.get("currency") or user_currency(user),
                    pending=False
                )
                db.add(transaction)
                db.commit()
                print(f"[Webhook] Transaction created for {email}: {description} - {amount}")

    return {"status": "ok"}


@router.post("/paystack")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive transaction notifications from Paystack"""
    payload = await request.json()
    signature = request.headers.get("x-paystack-signature", "")

    event = payload.get("event")
    data = payload.get("data", {})

    webhook_secret = settings.PAYSTACK_WEBHOOK_SECRET or settings.PAYSTACK_SECRET_KEY
    if not webhook_secret:
        raise HTTPException(503, "Webhook is not configured")
    if webhook_secret:
        computed = hmac.new(
            webhook_secret.encode('utf-8'),
            (await request.body()),
            hashlib.sha512
        ).hexdigest()
        if not signature or not hmac.compare_digest(computed, signature):
            raise HTTPException(401, "Invalid signature")

    if event == "charge.success":
        customer = data.get("customer", {})
        email = customer.get("email")
        if email:
            user = db.query(User).filter_by(email=email).first()
            if user:
                transaction_id = str(data.get("id")) if data.get("id") is not None else None
                if transaction_id and db.query(Transaction.id).filter_by(transaction_id=transaction_id).first():
                    return {"status": "ok"}
                description = data.get("metadata", {}).get("description", "Paystack payment")
                amount = data.get("amount", 0) / 100  # Paystack uses kobo
                category, confidence = ai_service.categorize_transaction(description)

                transaction = Transaction(
                    user_id=user.id,
                    description=description,
                    amount=amount,
                    date=datetime.utcnow(),
                    datetime=datetime.utcnow(),
                    category=category,
                    ml_confidence=confidence,
                    transaction_id=transaction_id,
                    currency=data.get("currency") or user_currency(user),
                    pending=False
                )
                db.add(transaction)
                db.commit()
                print(f"[Webhook] Transaction created for {email}: {description} - {amount}")

    return {"status": "ok"}

@router.post("/plaid")
async def plaid_webhook(request: Request):
    """Receive transaction updates from Plaid"""
    payload = await request.json()

    webhook_type = payload.get("webhook_type")
    webhook_code = payload.get("webhook_code")

    if webhook_type == "TRANSACTIONS" and webhook_code == "DEFAULT_UPDATE":
        item_id = payload.get("item_id")
        # Sync transactions for this item
        # Find user by item_id and trigger sync
        print(f"[Webhook] Plaid transactions update for item: {item_id}")

    return {"status": "ok"}
