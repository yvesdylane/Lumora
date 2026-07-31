from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.ownership import verifyTimelineOwnership
from core.timeline import tracks as tracksCore
from models.track import Track


async def createTrack(
    session: AsyncSession, timelineId: str, userId: str, kind: str
) -> Track:
    await verifyTimelineOwnership(session, timelineId, userId)
    return await tracksCore.addTrack(session, timelineId, kind)


async def listTracks(
    session: AsyncSession, timelineId: str, userId: str
) -> list[Track]:
    await verifyTimelineOwnership(session, timelineId, userId)
    return await tracksCore.getTracks(session, timelineId)


async def deleteTrack(
    session: AsyncSession, trackId: str, timelineId: str, userId: str
) -> None:
    await verifyTimelineOwnership(session, timelineId, userId)
    deleted = await tracksCore.deleteTrack(session, trackId)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Track not found",
        )
