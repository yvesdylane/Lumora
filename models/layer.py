from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Layer(BaseModel):
    id: str
    trackId: str
    layerType: str
    params: dict
    source: str
    position: int
    createdAt: datetime
    updatedAt: datetime

    model_config = {"from_attributes": True}
