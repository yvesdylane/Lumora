from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.timeline.models import ProjectRow
from models.project import Project


async def createProject(session: AsyncSession, name: str, userId: str) -> Project:
    row = ProjectRow(name=name, user_id=uuid.UUID(userId))
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def getProject(session: AsyncSession, projectId: str) -> Project | None:
    row = await session.get(ProjectRow, uuid.UUID(projectId))
    return _toModel(row) if row else None


async def listProjects(session: AsyncSession, userId: str) -> list[Project]:
    result = await session.execute(
        select(ProjectRow).where(ProjectRow.user_id == uuid.UUID(userId))
    )
    return [_toModel(r) for r in result.scalars().all()]


async def updateProject(session: AsyncSession, projectId: str, name: str) -> Project | None:
    row = await session.get(ProjectRow, uuid.UUID(projectId))
    if not row:
        return None
    row.name = name
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def deleteProject(session: AsyncSession, projectId: str) -> bool:
    row = await session.get(ProjectRow, uuid.UUID(projectId))
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


def _toModel(row: ProjectRow) -> Project:
    return Project(
        id=str(row.id),
        name=row.name,
        userId=str(row.user_id),
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )
