from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateLayerRequest(BaseModel):
    layerType: str
    params: dict
    source: str = "manual"


class UpdateLayerRequest(BaseModel):
    params: dict


class LayerResponse(BaseModel):
    id: str
    trackId: str
    layerType: str
    params: dict
    source: str
    position: int
    createdAt: datetime
    updatedAt: datetime
    model_config = {"from_attributes": True}
