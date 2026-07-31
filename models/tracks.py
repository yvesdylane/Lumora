from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateTrackRequest(BaseModel):
    kind: str


class TrackResponse(BaseModel):
    id: str
    timelineId: str
    kind: str
    position: int
    createdAt: datetime
    model_config = {"from_attributes": True}
