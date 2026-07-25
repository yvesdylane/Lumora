from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from controllers import layers as layersController
from core.database import getSession
from models.layers import CreateLayerRequest, UpdateLayerRequest, LayerResponse

router = APIRouter(prefix="/api/tracks/{trackId}/layers", tags=["layers"])


@router.post("/", response_model=LayerResponse, status_code=status.HTTP_201_CREATED)
async def createLayer(
    trackId: str,
    data: CreateLayerRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    layer = await layersController.createLayer(
        session, trackId, data.layerType, data.params, data.source, str(user.id)
    )
    return LayerResponse.model_validate(layer)


@router.patch("/{layerId}", response_model=LayerResponse)
async def updateLayer(
    trackId: str,
    layerId: str,
    data: UpdateLayerRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    layer = await layersController.updateLayer(
        session, layerId, trackId, data.params, str(user.id)
    )
    return LayerResponse.model_validate(layer)


@router.delete("/{layerId}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteLayer(
    trackId: str,
    layerId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await layersController.deleteLayer(session, layerId, trackId, str(user.id))
