from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.timeline.models import LayerRow, TimelineRow, TrackRow
from models.timeline import Timeline


async def createTimeline(session: AsyncSession, projectId: str) -> Timeline:
    row = TimelineRow(project_id=uuid.UUID(projectId))
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def getTimelineByProjectId(session: AsyncSession, projectId: str) -> Timeline | None:
    result = await session.execute(
        select(TimelineRow)
        .options(selectinload(TimelineRow.tracks).selectinload(TrackRow.layers))
        .where(TimelineRow.project_id == uuid.UUID(projectId))
    )
    row = result.scalar_one_or_none()
    return _toModel(row) if row else None


async def getTimeline(session: AsyncSession, timelineId: str) -> Timeline | None:
    result = await session.execute(
        select(TimelineRow)
        .options(selectinload(TimelineRow.tracks).selectinload(TrackRow.layers))
        .where(TimelineRow.id == uuid.UUID(timelineId))
    )
    row = result.scalar_one_or_none()
    return _toModel(row) if row else None


async def deleteTimeline(session: AsyncSession, timelineId: str) -> bool:
    row = await session.get(TimelineRow, uuid.UUID(timelineId))
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


def _toModel(row: TimelineRow) -> Timeline:
    return Timeline(
        id=str(row.id),
        projectId=str(row.project_id),
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )
