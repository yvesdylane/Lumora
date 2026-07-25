from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Timeline(BaseModel):
    id: str
    projectId: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
