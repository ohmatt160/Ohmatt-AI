from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict, Optional


class BankConnectRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bank_code: str = Field(..., alias="bankCode")
    bank_name: str = Field(..., alias="bankName")

class BankTokenExchangeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bank_code: str = Field(..., alias="bankCode")
    bank_name: str = Field(..., alias="bankName")
    public_token: str = Field(..., alias="publicToken")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BankAccountVerificationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bank_code: str = Field(..., alias="bankCode", min_length=2, max_length=30)
    bank_name: str = Field(..., alias="bankName", min_length=1, max_length=200)
    account_number: str = Field(..., alias="accountNumber", pattern=r"^\d{6,20}$")
    account_bank: str = Field(..., alias="accountBank", pattern=r"^[A-Za-z0-9_-]{2,20}$")

class BankDisconnectRequest(BaseModel):
    id: int = Field(...)

class BankAccountResponse(BaseModel):
    id: int
    connection_id: Optional[int]
    institution_name: str
    bankName: str
    account_name: str
    account_type: str
    accountMask: Optional[str]
    balance_available: Optional[float]
    balance_current: Optional[float]
    currency: str
    status: str


class CategoryPayload(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field("#4F46E5", max_length=20)


class BudgetPayload(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    month: str = Field(..., pattern=r"^\d{4}-\d{2}$")
    amount: float = Field(..., gt=0)
    alert_threshold: float = Field(0.8, ge=0.1, le=1)


class RecurringPayload(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount: float
    category: Optional[str] = None
    frequency: str = Field("monthly", pattern="^(weekly|monthly|yearly)$")
    next_date: str
    is_active: bool = True


class OnboardingPayload(BaseModel):
    completed: bool = True


class PushPayload(BaseModel):
    enabled: bool = True
