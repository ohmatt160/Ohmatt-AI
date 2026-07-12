import re
from typing import Iterable

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.utils.currency import format_currency


class TransactionContextService:
    """Build verified, user-scoped AI context from the complete transaction ledger."""

    _stop_words = {
        "about", "after", "before", "could", "from", "have", "into", "money",
        "show", "spend", "spent", "that", "their", "there", "these", "this",
        "transaction", "transactions", "what", "when", "where", "which", "with",
    }

    @classmethod
    def build(cls, db: Session, user_id: int, currency: str, message: str = "") -> str:
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
            .filter(Transaction.user_id == user_id)
            .one()
        )

        if not count:
            return "Verified ledger coverage: 0 transactions. No financial claims can be made."

        category_rows = (
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

        details = cls._relevant_details(db, user_id, message)
        lines = [
            f"Verified ledger coverage: all {count} transactions from "
            f"{first_date.isoformat() if first_date else 'unknown'} to "
            f"{last_date.isoformat() if last_date else 'unknown'}.",
            f"All-ledger expenses: {format_currency(float(expenses or 0), currency)}.",
            f"All-ledger income: {format_currency(float(income or 0), currency)}.",
            "Complete category aggregates (every transaction contributes):",
        ]
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
    def _relevant_details(cls, db: Session, user_id: int, message: str) -> list[tuple]:
        columns = (
            Transaction.id,
            Transaction.date,
            Transaction.description,
            Transaction.amount,
            Transaction.user_category,
            Transaction.category,
        )
        base = db.query(*columns).filter(Transaction.user_id == user_id)
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
