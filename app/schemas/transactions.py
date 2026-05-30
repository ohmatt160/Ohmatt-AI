from typing import Optional

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    description: str = Field(..., min_length=1)
    amount: float = Field(...)
    date: Optional[str] = Field(None, description="Format: YYYY-MM-DD HH:MM")


class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: float
    date: Optional[str]
    category: Optional[str]
    ml_confidence: Optional[float]
    currency: str
    pending: bool
    merchant_name: Optional[str]
