from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.timeline.models import TrackRow
from models.track import Track


async def addTrack(session: AsyncSession, timelineId: str, kind: str) -> Track:
    result = await session.execute(
        select(TrackRow.position)
        .where(TrackRow.timeline_id == uuid.UUID(timelineId))
        .order_by(TrackRow.position.desc())
        .limit(1)
    )
    lastPos = result.scalar_one_or_none()
    nextPos = (lastPos or -1) + 1

    row = TrackRow(
        timeline_id=uuid.UUID(timelineId),
        kind=kind,
        position=nextPos,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def getTracks(session: AsyncSession, timelineId: str) -> list[Track]:
    result = await session.execute(
        select(TrackRow)
        .where(TrackRow.timeline_id == uuid.UUID(timelineId))
        .order_by(TrackRow.position)
    )
    return [_toModel(r) for r in result.scalars().all()]


async def deleteTrack(session: AsyncSession, trackId: str) -> bool:
    row = await session.get(TrackRow, uuid.UUID(trackId))
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


def _toModel(row: TrackRow) -> Track:
    return Track(
        id=str(row.id),
        timelineId=str(row.timeline_id),
        kind=row.kind,
        position=row.position,
        createdAt=row.created_at,
    )
