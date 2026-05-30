# app/routes/webhooks.py
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
import hashlib, hmac, json
from app.extensions import db_session
from app.models.transaction import Transaction
from app.models.user import User
from app.services.ai_service import ai_service
from app.config import settings

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/flutterwave")
async def flutterwave_webhook(request: Request):
    """Receive transaction notifications from Flutterwave"""
    payload = await request.json()
    signature = request.headers.get("verif-hash", "")

    # Verify signature (add your secret hash)
    if signature != settings.FLUTTERWAVE_SECRET_HASH:
        raise HTTPException(401, "Invalid signature")

    event = payload.get("event")
    data = payload.get("data", {})

    if event == "charge.completed" and data.get("status") == "successful":
        # Find user by customer email
        customer = data.get("customer", {})
        email = customer.get("email")
        if email:
            user = db_session.query(User).filter_by(email=email).first()
            if user:
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
                    transaction_id=data.get("id"),
                    currency=data.get("currency", "NGN"),
                    pending=False
                )
                db_session.add(transaction)
                db_session.commit()
                print(f"[Webhook] Transaction created for {email}: {description} - {amount}")

    return {"status": "ok"}


@router.post("/paystack")
async def paystack_webhook(request: Request):
    """Receive transaction notifications from Paystack"""
    payload = await request.json()
    signature = request.headers.get("x-paystack-signature", "")

    event = payload.get("event")
    data = payload.get("data", {})

    # Verify Paystack signature
    if settings.PAYSTACK_SECRET_KEY:
        computed = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            (await request.body()),
            hashlib.sha512
        ).hexdigest()
        if signature and not hmac.compare_digest(computed, signature):
            raise HTTPException(401, "Invalid signature")

    if event == "charge.success":
        customer = data.get("customer", {})
        email = customer.get("email")
        if email:
            user = db_session.query(User).filter_by(email=email).first()
            if user:
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
                    transaction_id=str(data.get("id")),
                    currency=data.get("currency", "NGN"),
                    pending=False
                )
                db_session.add(transaction)
                db_session.commit()
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