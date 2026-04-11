from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    contact: str = Field(min_length=3, max_length=255)
    service: str = Field(min_length=2, max_length=255)
    comment: Optional[str] = Field(default=None, max_length=2000)


class LeadOut(BaseModel):
    id: int
    name: str
    contact: str
    service: str
    comment: Optional[str]
    status: str
    created_at: str


class LeadStatusUpdate(BaseModel):
    status: str = Field(pattern="^(new|in_progress|booked|done|canceled)$")


class LoginInput(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"