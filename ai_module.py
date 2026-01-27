import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from collections import defaultdict
import numpy as np

top_n = 3

# Load ML models if available
try:
    vectorizer = joblib.load("vectorizer.pkl")
    clf = joblib.load("transaction_model.pkl")
except:
    vectorizer = TfidfVectorizer()
    clf = RandomForestClassifier()

def categorize_transaction(description):
    if not description:
        return "Uncategorized", 0.0
    X = vectorizer.transform([description])

    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba(X)[0]
        classes = clf.classes_
        top_indices = np.argsort(proba)[::-1][:top_n]
        top_categories = [(classes[i], float(proba[i])) for i in top_indices]
        # Return the top category and its confidence
        return top_categories[0][0], top_categories[0][1]
    else:
        category = clf.predict(X)[0]
        confidence = max(clf.predict_proba(X)[0])
        return [(category, 1.0)], confidence



def analyze_spending(user_transactions):
    summary = defaultdict(float)
    for t in user_transactions:
        summary[t.category or "Uncategorized"] += t.amount

    total = sum(summary.values())
    insights = []
    for cat, amt in summary.items():
        perc = (amt / total) * 100 if total else 0
        insights.append(f"You spent ${amt:.2f} on {cat} ({perc:.0f}% of total)")

    if len(user_transactions) > 5:
        amounts = [[t.amount] for t in user_transactions]
        iso = IsolationForest(contamination=0.1)
        iso.fit(amounts)
        preds = iso.predict(amounts)
        anomalies = [t for t, p in zip(user_transactions, preds) if p == -1]
        if anomalies:
            insights.append(f"⚠️ {len(anomalies)} unusual transaction(s) detected.")
            for t in anomalies:
                insights.append(f" - {t.description}: ${t.amount:.2f}")

    return insights
