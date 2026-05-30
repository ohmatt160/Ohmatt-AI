# app/services/insight_service.py - NEW APPROACH
from openai import OpenAI
from app.config import settings
from datetime import datetime, timedelta

from app.models.insight import Insight
from app.models.transaction import Transaction

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=settings.NVIDIA_API_KEY
)


class InsightService:
    @staticmethod
    def generate_insights(db, user):
        """Use LLM to analyze transactions and generate insights"""
        month_ago = datetime.utcnow() - timedelta(days=30)
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.date >= month_ago
        ).all()

        if len(transactions) < 3:
            return []

        # Get user's currency
        user_currency = (user.preferences or {}).get("currency", "USD")
        symbol_map = {"USD": "$", "NGN": "₦", "GBP": "£", "EUR": "€", "GHS": "₵", "KES": "KSh"}
        symbol = symbol_map.get(user_currency, "$")

        # Build transaction summary for the LLM
        tx_summary = "\n".join([
            f"- {t.date.strftime('%b %d')}: {t.description} - {symbol}{t.amount:,.2f} ({t.category or 'Uncategorized'})"
            for t in transactions[-20:]
        ])

        total = sum(t.amount for t in transactions)

        prompt = f"""Analyze these transactions and return 2-3 insights as JSON array.

    User's currency: {user_currency} (symbol: {symbol})

    Transactions:
    {tx_summary}

    Total spent: {symbol}{total:,.2f} in 30 days

    Return JSON like:
    [
      {{"type": "spending_pattern|anomaly|suggestion|forecast", "title": "short title", "description": "1-2 sentence insight using {symbol}", "severity": "low|medium|high"}}
    ]

    Rules:
    - Use {symbol} for all money amounts
    - Find actual patterns, don't make up data
    - If you see a large transaction compared to others, flag it as anomaly
    - If a category dominates, mention it
    - Give actionable suggestions based on real spending
    - Keep descriptions under 200 characters
    - Only return JSON, no other text"""

        try:
            response = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,  # Low = more factual
            )

            import json
            insights = json.loads(response.choices[0].message.content)

            # Save to database
            for insight_data in insights:
                insight = Insight(
                    user_id=user.id,
                    type=insight_data.get("type", "spending_pattern"),
                    title=insight_data["title"],
                    description=insight_data["description"],
                    severity=insight_data.get("severity", "low"),
                )
                db.add(insight)
            db.commit()

            return insights
        except Exception as e:
            print(f"LLM Insight error: {e}")
            return []