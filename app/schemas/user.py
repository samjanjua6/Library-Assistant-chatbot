from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class UserSignup(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(
        min_length=5,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )
    password: str = Field(min_length=6, max_length=128)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}
