import os
import logging
import re
import joblib
import numpy as np
from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.utils.currency import format_currency

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS = {
    "Food & Dining": ("restaurant", "cafe", "coffee", "uber eats", "doordash", "food", "grocery", "market", "supermarket", "mcdonald", "kfc", "pizza", "bakery"),
    "Transportation": ("uber", "bolt", "lyft", "taxi", "fuel", "petrol", "gas station", "parking", "bus", "train", "airline", "flight"),
    "Shopping": ("amazon", "walmart", "target", "shop", "store", "clothing", "fashion", "ikea", "electronics"),
    "Bills & Utilities": ("electric", "water bill", "internet", "utility", "power", "telecom", "airtime", "data plan", "rent"),
    "Entertainment": ("netflix", "spotify", "cinema", "movie", "concert", "gaming", "playstation", "steam"),
    "Health": ("pharmacy", "hospital", "clinic", "doctor", "medical", "health", "dental"),
    "Travel": ("hotel", "airbnb", "booking.com", "travel", "resort"),
    "Education": ("school", "tuition", "university", "course", "books"),
    "Income": ("salary", "payroll", "interest payment", "dividend", "refund"),
    "Transfers": ("transfer", "wire", "cash withdrawal", "atm"),
}


class AIService:
    def __init__(self):
        service_dir = os.path.dirname(os.path.abspath(__file__))
        vectorizer_path = os.path.join(service_dir, "vectorizer.pkl")
        model_path = os.path.join(service_dir, "transaction_model.pkl")

        self.vectorizer = None
        self.clf = None
        try:
            self.vectorizer = joblib.load(vectorizer_path)
            self.clf = joblib.load(model_path)
            if not hasattr(self.clf, "classes_"):
                self.vectorizer = self.clf = None
        except Exception as exc:
            logger.info("Transaction model unavailable; using category rules (%s)", type(exc).__name__)

        self.top_n = 3
        self.service_dir = service_dir

    def categorize_transaction(self, description: str) -> Tuple[str, float]:
        if not description:
            return "Uncategorized", 0.0
        normalized = re.sub(r"[^a-z0-9]+", " ", description.lower()).strip()
        # Merchant and descriptor rules provide predictable behavior even when
        # no trained artifact is deployed or model confidence is low.
        for category, terms in CATEGORY_KEYWORDS.items():
            if any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in terms):
                return category, 0.85
        if self.vectorizer is not None and self.clf is not None:
            try:
                X = self.vectorizer.transform([description])
                if hasattr(self.clf, "predict_proba"):
                    proba = self.clf.predict_proba(X)[0]
                    classes = self.clf.classes_
                    top_indices = np.argsort(proba)[::-1][:self.top_n]
                    confidence = float(proba[top_indices[0]])
                    predicted = str(classes[top_indices[0]]).strip()
                    if confidence >= 0.35 and predicted and predicted.lower() != "uncategorized":
                        return predicted, confidence
                else:
                    category = str(self.clf.predict(X)[0]).strip()
                    if category and category.lower() != "uncategorized":
                        return category, 1.0
            except Exception:
                logger.exception("Transaction categorization model failed")
        # Keep unknown merchants visible in reports without claiming a confident
        # semantic category. The low score makes the classification auditable.
        return "Other", 0.15

    def analyze_spending(
        self,
        db: Session,
        user_id: int,
        currency: str,
    ) -> List[str]:
        rows = (
            db.query(
                func.coalesce(Transaction.user_category, Transaction.category, "Uncategorized"),
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .filter(Transaction.user_id == user_id)
            .group_by(func.coalesce(Transaction.user_category, Transaction.category, "Uncategorized"))
            .order_by(func.count(Transaction.id).desc())
            .all()
        )
        return [
            f"{category}: {count} transactions, net {format_currency(float(amount or 0), currency)}"
            for category, count, amount in rows
        ]

ai_service = AIService()
