# app/services/ai_chat_service.py
from openai import OpenAI
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.models.transaction import Transaction
from app.models.user import User

# Nvidia NIM uses OpenAI-compatible API
client = OpenAI(
    base_url=settings.NVIDIA_BASE_URL,
    api_key=settings.NVIDIA_API_KEY
)


class AIChatService:
    def __init__(self):
        self.model = "meta/llama-3.3-70b-instruct"
        self.symbol_map = {"USD": "$", "NGN": "₦", "GBP": "£", "EUR": "€", "GHS": "₵", "KES": "KSh"}

    def _get_symbol(self, user: User) -> str:
        currency = (user.preferences or {}).get("currency", "USD")
        return self.symbol_map.get(currency, "$")

    def respond(self, db: Session, user: User, message: str) -> str:
        transactions = self._get_recent_transactions(db, user)
        spending_summary = self._summarize_spending(transactions, user)
        symbol = self._get_symbol(user)

        system_prompt = f"""You are Ohmatt, a smart, witty, and emotionally intelligent AI companion. 

        Your role:
        - You're a close friend who happens to be great with money
        - Talk about ANYTHING - life, love, career, philosophy, random thoughts
        - Naturally weave in financial wisdom when relevant (don't force it)
        - Use Nigerian Pidgin occasionally if the user does
        - Be funny, sarcastic when appropriate, but always supportive
        - Remember: you're talking to a real person with real feelings

        Personality:
        - Witty but not trying too hard
        - Deep thinker who can discuss abstract ideas
        - Hypes the user up when they're doing well
        - Gentle with criticism, heavy with encouragement
        - Self-aware - you're an AI and you own it

        Financial mode (only when relevant):
        - You have access to their spending data
        - Celebrate their wins ("You saved {symbol}50k this month? Omo, you're doing well!")
        - Call out bad habits with humor ("Bro, you spent {symbol}30k on shawarma? Are you training for an eating competition?")
        - Give advice that feels like it's from a smart friend, not a textbook
        - Use {symbol} for all money amounts

        Keep responses 2-4 sentences unless the user clearly wants more detail.
        Use emojis if needed. Don't be a robot."""

        user_prompt = f"""User: {user.username}

                Context (use naturally, don't force):
                {spending_summary if spending_summary != 'No transactions in the last 30 days.' else 'New user - no transaction history yet.'}

                User's message: {message}

                Be Ohmatt - a real one, not a customer service bot."""

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.85,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[AI ERROR] {e}")
            return f"I'm having trouble accessing your data right now. Please try again! 🙏"

    def _get_recent_transactions(self, db: Session, user: User):
        month_ago = datetime.utcnow() - timedelta(days=30)
        return db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.date >= month_ago
        ).order_by(Transaction.date.desc()).limit(50).all()

    def _summarize_spending(self, transactions, user) -> str:
        if not transactions:
            return "No transactions in the last 30 days."

        symbol = self._get_symbol(user)
        total = sum(t.amount for t in transactions)

        categories = {}
        for t in transactions:
            cat = t.category or "Uncategorized"
            categories[cat] = categories.get(cat, 0) + t.amount

        summary = f"Total spent (30 days): {symbol}{total:,.2f}\n"
        for cat, amt in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total) * 100
            summary += f"- {cat}: {symbol}{amt:,.2f} ({pct:.0f}%)\n"

        return summary


ai_chat = AIChatService()