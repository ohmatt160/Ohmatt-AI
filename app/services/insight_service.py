"""Fast, ledger-grounded insight generation without a network call per write."""
import logging
from datetime import datetime, timedelta

from sqlalchemy import case, func

from app.models.insight import Insight
from app.models.transaction import Transaction
from app.utils.currency import format_currency
from app.utils.i18n import user_currency

logger = logging.getLogger(__name__)


class InsightService:
    @staticmethod
    def generate_insights(db, user):
        """Create at most two current-month insights from database aggregates."""
        currency = user_currency(user)
        now = datetime.utcnow()
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        current_period_end = min(now, next_month)
        previous_start = (start - timedelta(days=1)).replace(day=1)
        comparison_end = min(previous_start + timedelta(days=now.day), start)
        current_rows = db.query(
            func.coalesce(Transaction.category, "Other"),
            func.count(Transaction.id),
            func.coalesce(func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)), 0),
        ).filter(
            Transaction.user_id == user.id,
            Transaction.date >= start,
            Transaction.date < current_period_end,
        ).group_by(Transaction.category).order_by(func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).desc()).all()
        if not current_rows:
            return []

        current_total = sum(float(row[2] or 0) for row in current_rows)
        previous_total = float(db.query(
            func.coalesce(func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)), 0)
        ).filter(
            Transaction.user_id == user.id,
            Transaction.date >= previous_start,
            Transaction.date < comparison_end,
        ).scalar() or 0)

        candidates = []
        if previous_total > 0 and current_total >= previous_total * 1.2:
            change = round((current_total - previous_total) / previous_total * 100)
            candidates.append({
                "type": "spending_pattern",
                "title": "Month-to-date spending is up",
                "description": f"Spending so far this month is {change}% higher than last month's comparable period. Current total: {format_currency(current_total, currency)}.",
                "severity": "medium" if change >= 40 else "low",
            })
        category, _, amount = current_rows[0]
        if len(current_rows) > 1 and current_total > 0 and float(amount or 0) / current_total >= 0.5:
            candidates.append({
                "type": "spending_pattern",
                "title": f"{category} is your largest category this month",
                "description": f"{format_currency(float(amount or 0), currency)} of this month's recorded spending is in {category}.",
                "severity": "low",
            })

        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        saved = []
        for item in candidates[:2]:
            duplicate = db.query(Insight.id).filter(
                Insight.user_id == user.id,
                Insight.title == item["title"],
                Insight.created_at >= today,
            ).first()
            if duplicate:
                continue
            insight = Insight(
                user_id=user.id,
                type=item["type"],
                title=item["title"],
                description=item["description"][:200],
                severity=item["severity"],
            )
            db.add(insight)
            saved.append(item)
        if saved:
            db.commit()
        return saved
