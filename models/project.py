from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Project(BaseModel):
    id: str
    name: str
    userId: str
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
