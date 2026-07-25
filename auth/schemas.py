from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: uuid.UUID
    email: str
    createdAt: datetime
    model_config = {"from_attributes": True}


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    accessToken: str
    refreshToken: str
    tokenType: str = "bearer"


class RefreshRequest(BaseModel):
    refreshToken: str
