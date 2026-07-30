from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateJobRequest(BaseModel):
    projectId: str
    tier: int
    jobType: str
    prompt: str = ""


class JobResponse(BaseModel):
    id: str
    projectId: str
    tier: int
    jobType: str
    prompt: str
    status: str
    result: dict | None = None
    error: str | None = None
    attempts: int = 0
    maxAttempts: int = 3
    createdAt: datetime
    updatedAt: datetime


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
