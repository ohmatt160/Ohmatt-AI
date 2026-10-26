import re
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.utils.currency import format_currency


class TransactionContextService:
    """Build verified, user-scoped AI context from the complete transaction ledger."""

    _stop_words = {
        "about", "after", "am", "are", "before", "can", "compare", "compared", "could",
        "did", "do", "doing", "for", "from", "have", "higher", "how", "i", "into", "is",
        "less", "lower", "me", "money", "more", "my", "much", "of", "please",
        "show", "spend", "spent", "that", "their", "there", "these", "this", "was", "were",
        "transaction", "transactions", "what", "when", "where", "which", "with",
        "expense", "expenses", "spending", "spent", "cost", "costs", "tell", "analyze",
        "analyse", "insight", "insights", "trend", "trends", "month", "week", "today", "pay",
        "than", "versus", "vs", "you", "food", "dining", "transport", "transportation",
        "shopping", "bill", "bills", "utility", "utilities", "entertainment", "health", "other",
        "travel", "education", "income", "transfer", "transfers", "restaurant", "restaurants",
        "grocery", "groceries", "fuel", "subscription", "subscriptions",
        "expensive", "costly", "pricey", "purchase", "purchases",
    }

    @classmethod
    def build(cls, db: Session, user_id: int, currency: str, message: str = "") -> str:
        now = datetime.utcnow()
        lowered = (message or "").lower()
        compare_months = (
            "last month" in lowered
            and ("this month" in lowered or re.search(r"\b(compare|compared|versus|vs)\b", lowered))
        )
        if compare_months:
            period = "this month vs last month"
            this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start = (this_month - timedelta(days=1)).replace(day=1)
            end = now
        elif re.search(r"\b(today|this day)\b", lowered):
            period = "today"
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif re.search(r"\b(this week|weekly|past 7 days|last 7 days)\b", lowered):
            period = "this week"
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif re.search(r"\b(last week)\b", lowered):
            period = "last week"
            end = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            start = end - timedelta(days=7)
        elif re.search(r"\b(last month)\b", lowered):
            period = "last month"
            this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = this_month
            start = (this_month - timedelta(days=1)).replace(day=1)
        elif re.search(r"\b(all time|overall|ever|since (?:i|the) started)\b", lowered):
            period, start, end = "all time", None, None
        elif cls._search_terms(message):
            # Merchant-specific questions should search the full history.
            period, start, end = "all time", None, None
        else:
            period = "this month"
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)

        scope_filter = [Transaction.user_id == user_id]
        if start is not None:
            scope_filter.append(Transaction.date >= start)
        if end is not None:
            scope_filter.append(Transaction.date < end)
        count, first_date, last_date, expenses, income = (
            db.query(
                func.count(Transaction.id),
                func.min(Transaction.date),
                func.max(Transaction.date),
                func.coalesce(
                    func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((Transaction.amount < 0, -Transaction.amount), else_=0)),
                    0,
                ),
            )
            .filter(*scope_filter)
            .one()
        )

        if not count:
            return f"Verified ledger scope: {period} (UTC), 0 transactions. No financial claims can be made."

        category_rows = (
            db.query(
                func.coalesce(Transaction.user_category, Transaction.category, "Uncategorized"),
                func.count(Transaction.id),
                func.coalesce(func.sum(Transaction.amount), 0),
            )
            .filter(*scope_filter)
            .group_by(func.coalesce(Transaction.user_category, Transaction.category, "Uncategorized"))
            .order_by(func.count(Transaction.id).desc())
            .all()
        )

        details = cls._relevant_details(db, user_id, message, start=start, end=end)
        lines = [
            f"Verified ledger scope: {period} (UTC), all {count} transactions in scope from "
            f"{first_date.isoformat() if first_date else 'unknown'} to "
            f"{last_date.isoformat() if last_date else 'unknown'}.",
            f"Expenses in this period: {format_currency(float(expenses or 0), currency)}.",
            f"Income in this period: {format_currency(float(income or 0), currency)}.",
            "Complete category aggregates for this period (every matching transaction contributes):",
        ]
        if compare_months:
            previous_start = start
            current_start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_end = min(previous_start + timedelta(days=now.day), current_start)
            comparison_summaries = []
            for label, period_start, period_end in (
                ("Last month comparable period", previous_start, previous_end),
                ("This month to date", current_start, end),
            ):
                period_count, period_expenses, period_income = db.query(
                    func.count(Transaction.id),
                    func.coalesce(func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)), 0),
                    func.coalesce(func.sum(case((Transaction.amount < 0, -Transaction.amount), else_=0)), 0),
                ).filter(
                    Transaction.user_id == user_id,
                    Transaction.date >= period_start,
                    Transaction.date < period_end,
                ).one()
                comparison_summaries.append(
                    f"- {label}: {period_count} transactions, expenses "
                    f"{format_currency(float(period_expenses or 0), currency)}, income "
                    f"{format_currency(float(period_income or 0), currency)}"
                )
            lines.append("Month comparison, with separate verified totals:")
            lines.extend(comparison_summaries)
        lines.extend(
            f"- {category}: {row_count} transactions, net "
            f"{format_currency(float(net_amount or 0), currency)}"
            for category, row_count, net_amount in category_rows
        )
        if details:
            lines.append("Retrieved transaction details relevant to this request:")
            lines.extend(cls._format_details(details, currency))
        else:
            lines.append(
                "No individual transaction matched the request. Do not invent a merchant, date, "
                "description, category, or amount."
            )
        return "\n".join(lines)

    @classmethod
    def _relevant_details(
        cls, db: Session, user_id: int, message: str,
        *, start: datetime | None = None, end: datetime | None = None,
    ) -> list[tuple]:
        columns = (
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.amount,
            Transaction.user_category,
            Transaction.category,
        )
        base = db.query(*columns).filter(Transaction.user_id == user_id)
        if start is not None:
            base = base.filter(Transaction.date >= start)
        if end is not None:
            base = base.filter(Transaction.date < end)
        rows = base.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(25).all()
        rows += base.order_by(func.abs(Transaction.amount).desc(), Transaction.id.desc()).limit(25).all()

        terms = cls._search_terms(message)
        if terms:
            predicates = [Transaction.description.ilike(f"%{term}%") for term in terms]
            rows += (
                base.filter(or_(*predicates))
                .order_by(Transaction.date.desc(), Transaction.id.desc())
                .limit(50)
                .all()
            )

        deduplicated = {}
        for row in rows:
            deduplicated[row[0]] = row
        return list(deduplicated.values())

    @classmethod
    def _search_terms(cls, message: str) -> list[str]:
        terms = {
            token.lower()
            for token in re.findall(r"[A-Za-z0-9]{3,40}", message or "")
            if token.lower() not in cls._stop_words
        }
        return sorted(terms)[:8]

    @staticmethod
    def _format_details(rows: Iterable[tuple], currency: str) -> list[str]:
        return [
            f"- id={row_id}; date={date.isoformat() if date else 'unknown'}; "
            f"description={description or 'Unavailable'}; "
            f"amount={format_currency(float(amount or 0), currency)}; "
            f"category={user_category or category or 'Uncategorized'}"
            for row_id, date, description, amount, user_category, category in rows
        ]


transaction_context_service = TransactionContextService()
