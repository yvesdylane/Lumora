from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GenerationJob(BaseModel):
    id: str
    projectId: str
    tier: int
    jobType: str
    prompt: str
    status: str = "pending"
    result: dict | None = None
    error: str | None = None
    attempts: int = 0
    maxAttempts: int = 3
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
