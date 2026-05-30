# app/schemas/message.py
from pydantic import BaseModel, Field
from typing import Optional

class MessageCreate(BaseModel):
    receiver_username: str = Field(...)
    content: str = Field(..., min_length=1)

class MessageEdit(BaseModel):
    content: str = Field(..., min_length=1)

class ForwardRequest(BaseModel):
    receiver_username: str = Field(...)

class MessageResponse(BaseModel):
    id: int
    sender: str
    receiver: str
    content: str
    timestamp: str
    is_read: bool
    status: Optional[str] = None
    is_edited: bool = False
    is_deleted: bool = False
