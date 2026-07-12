import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.utils.currency import format_currency


class AIService:
    def __init__(self):
        service_dir = os.path.dirname(os.path.abspath(__file__))
        vectorizer_path = os.path.join(service_dir, "vectorizer.pkl")
        model_path = os.path.join(service_dir, "transaction_model.pkl")

        try:
            self.vectorizer = joblib.load(vectorizer_path)
            self.clf = joblib.load(model_path)
        except:
            csv_path = os.path.join(service_dir, "..", "..", "transactions.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                self.vectorizer = TfidfVectorizer()
                X = self.vectorizer.fit_transform(df['description'].fillna(''))
                self.clf = RandomForestClassifier()
                self.clf.fit(X, df['category'])
                joblib.dump(self.vectorizer, vectorizer_path)
                joblib.dump(self.clf, model_path)
            else:
                self.vectorizer = TfidfVectorizer()
                self.clf = RandomForestClassifier()

        self.top_n = 3
        self.service_dir = service_dir

    def categorize_transaction(self, description: str) -> Tuple[str, float]:
        if not description:
            return "Uncategorized", 0.0
        try:
            X = self.vectorizer.transform([description])
            if hasattr(self.clf, "predict_proba"):
                proba = self.clf.predict_proba(X)[0]
                classes = self.clf.classes_
                top_indices = np.argsort(proba)[::-1][:self.top_n]
                return classes[top_indices[0]], float(proba[top_indices[0]])
            else:
                category = self.clf.predict(X)[0]
                return category, 1.0
        except:
            return "Uncategorized", 0.0

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

    def retrain_from_corrections(self, corrections: List[Transaction]) -> int:
        rows = [
            {
                "description": tx.description or "",
                "category": tx.user_category or tx.category or "Uncategorized",
            }
            for tx in corrections
            if tx.description and (tx.user_category or tx.category)
        ]
        if not rows:
            return 0

        df = pd.DataFrame(rows)
        self.vectorizer = TfidfVectorizer()
        X = self.vectorizer.fit_transform(df["description"].fillna(""))
        self.clf = RandomForestClassifier()
        self.clf.fit(X, df["category"])
        joblib.dump(self.vectorizer, os.path.join(self.service_dir, "vectorizer.pkl"))
        joblib.dump(self.clf, os.path.join(self.service_dir, "transaction_model.pkl"))
        return len(rows)


ai_service = AIService()
