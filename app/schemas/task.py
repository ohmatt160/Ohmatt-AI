from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskBase(BaseModel):
    task: str = Field(..., min_length=1)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    time: str = Field(..., pattern=r"^\d{2}:\d{2}$")  # HH:MM


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    
    class Config:
        orm_mode = True