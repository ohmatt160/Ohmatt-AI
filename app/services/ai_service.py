import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from collections import defaultdict
import numpy as np
from typing import List, Tuple
from app.models.transaction import Transaction


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

    def analyze_spending(self, transactions: List[Transaction]) -> List[str]:
        summary = defaultdict(float)
        for t in transactions:
            summary[t.category or "Uncategorized"] += t.amount

        total = sum(summary.values())
        insights = []

        for cat, amt in summary.items():
            perc = (amt / total) * 100 if total else 0
            insights.append(f"You spent ${amt:.2f} on {cat} ({perc:.0f}% of total)")

        if len(transactions) > 5:
            amounts = [[t.amount] for t in transactions]
            iso = IsolationForest(contamination=0.1)
            iso.fit(amounts)
            preds = iso.predict(amounts)
            anomalies = [t for t, p in zip(transactions, preds) if p == -1]
            if anomalies:
                insights.append(f" {len(anomalies)} unusual transaction(s) detected.")
                for t in anomalies:
                    insights.append(f" - {t.description}: ${t.amount:.2f}")

        return insights


ai_service = AIService()