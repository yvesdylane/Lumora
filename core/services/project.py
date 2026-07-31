from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.timeline.projects import createProject
from core.timeline.timeline import createTimeline
from core.timeline.tracks import addTrack
from models.project import Project


async def setupProject(
    session: AsyncSession,
    name: str,
    userId: str,
) -> Project:
    project = await createProject(session, name, userId)

    timeline = await createTimeline(session, project.id)

    await addTrack(session, timeline.id, "video")
    await addTrack(session, timeline.id, "audio")
    await addTrack(session, timeline.id, "text")

    return project
