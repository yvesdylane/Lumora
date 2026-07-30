from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Export(BaseModel):
    id: str
    projectId: str
    timelineId: str
    status: str = "pending"
    outputFormat: str = "mp4"
    b2Key: str | None = None
    error: str | None = None
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
