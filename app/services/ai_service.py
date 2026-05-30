import os

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from collections import defaultdict
import numpy as np
from typing import List, Tuple
from app.models.transaction import Transaction


class AIService:
    def __init__(self):
        service_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_loaded = False

        try:
            self.vectorizer = joblib.load(os.path.join(service_dir, "vectorizer.pkl"))
            self.clf = joblib.load(os.path.join(service_dir, "transaction_model.pkl"))
            self.model_loaded = True
        except Exception as e:
            print(f"[WARNING] Could not load AI models: {e}")
            self.vectorizer = TfidfVectorizer()
            self.clf = RandomForestClassifier()

        self.top_n = 3

    def categorize_transaction(self, description: str) -> Tuple[str, float]:
        """Categorize a transaction description and return category with confidence"""
        if not description:
            return "Uncategorized", 0.0

        if not self.model_loaded:
            return self._categorize_with_keywords(description)

        X = self.vectorizer.transform([description])

        if hasattr(self.clf, "predict_proba"):
            proba = self.clf.predict_proba(X)[0]
            classes = self.clf.classes_
            top_indices = np.argsort(proba)[::-1][:self.top_n]
            top_categories = [(classes[i], float(proba[i])) for i in top_indices]
            return top_categories[0][0], top_categories[0][1]
        else:
            category = self.clf.predict(X)[0]
            confidence = 1.0
            return category, confidence

    def _categorize_with_keywords(self, description: str) -> Tuple[str, float]:
        text = description.lower()
        keyword_map = {
            "Food & Drink": ["coffee", "restaurant", "food", "meal", "pizza", "burger", "cafe", "drink"],
            "Transport": ["uber", "bolt", "taxi", "fuel", "gas", "bus", "train", "flight", "transport"],
            "Groceries": ["grocery", "supermarket", "market", "walmart", "costco", "groceries"],
            "Entertainment": ["netflix", "spotify", "movie", "cinema", "concert", "game", "streaming"],
            "Shopping": ["amazon", "store", "shopping", "clothing", "electronics", "target", "purchase"],
            "Healthcare": ["pharmacy", "doctor", "hospital", "clinic", "medicine", "dental"],
            "Fitness": ["gym", "fitness", "yoga", "trainer", "pilates"],
            "Education": ["course", "school", "tuition", "books", "exam", "university"],
            "Utilities": ["electric", "water", "internet", "utility", "bill", "phone"],
            "Income": ["salary", "payroll", "deposit", "income", "wage"],
        }

        for category, keywords in keyword_map.items():
            if any(keyword in text for keyword in keywords):
                return category, 0.55

        return "Uncategorized", 0.2

    def analyze_spending(self, transactions: List[Transaction]) -> List[str]:
        """Analyze spending patterns and return insights"""
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


# Singleton instance for reuse
ai_service = AIService()
