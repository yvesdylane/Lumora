from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.timeline.models import ProjectRow, TimelineRow


async def verifyProjectOwnership(
    session: AsyncSession, projectId: str, userId: str
) -> None:
    result = await session.execute(
        select(ProjectRow).where(ProjectRow.id == uuid.UUID(projectId))
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    if str(project.user_id) != userId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this project",
        )


async def verifyTimelineOwnership(
    session: AsyncSession, timelineId: str, userId: str
) -> None:
    result = await session.execute(
        select(TimelineRow, ProjectRow)
        .join(ProjectRow, TimelineRow.project_id == ProjectRow.id)
        .where(TimelineRow.id == uuid.UUID(timelineId))
    )
    row = result.first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline not found",
        )
    _timeline, project = row
    if str(project.user_id) != userId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this timeline",
        )
