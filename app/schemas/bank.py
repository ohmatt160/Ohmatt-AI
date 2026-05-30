from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict

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

    bank_code: str = Field(..., alias="bankCode")
    bank_name: str = Field(..., alias="bankName")
    account_number: str = Field(..., alias="accountNumber")
    account_bank: str = Field(..., alias="accountBank")

class BankDisconnectRequest(BaseModel):
    id: int = Field(...)
