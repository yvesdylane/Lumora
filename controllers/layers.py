from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.ownership import verifyTimelineOwnership
from core.timeline import layers as layersCore
from core.timeline.models import TrackRow
from models.layer import Layer


async def _getTimelineIdForTrack(
    session: AsyncSession, trackId: str
) -> str | None:
    result = await session.execute(
        select(TrackRow.timeline_id).where(TrackRow.id == uuid.UUID(trackId))
    )
    row = result.scalar_one_or_none()
    return str(row) if row else None


async def createLayer(
    session: AsyncSession,
    trackId: str,
    layerType: str,
    params: dict,
    source: str,
    userId: str,
) -> Layer:
    timelineId = await _getTimelineIdForTrack(session, trackId)
    if timelineId is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    await verifyTimelineOwnership(session, timelineId, userId)
    return await layersCore.addLayer(session, trackId, layerType, params, source)


async def updateLayer(
    session: AsyncSession,
    layerId: str,
    trackId: str,
    params: dict,
    userId: str,
) -> Layer:
    timelineId = await _getTimelineIdForTrack(session, trackId)
    if timelineId is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    await verifyTimelineOwnership(session, timelineId, userId)
    updated = await layersCore.updateLayer(session, layerId, params)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer not found",
        )
    return updated


async def deleteLayer(
    session: AsyncSession,
    layerId: str,
    trackId: str,
    userId: str,
) -> None:
    timelineId = await _getTimelineIdForTrack(session, trackId)
    if timelineId is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
    await verifyTimelineOwnership(session, timelineId, userId)
    deleted = await layersCore.deleteLayer(session, layerId)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Layer not found",
        )
