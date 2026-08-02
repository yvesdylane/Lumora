from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.timeline import layers as layersCore
from core.timeline import projects as projectCore
from core.timeline import timeline as timelineCore
from core.timeline import tracks as tracksCore
from models.project import Project
from models.timelineDetail import TimelineDetail, TrackDetail

DEFAULT_TRACK_KINDS = ["video", "audio", "text", "effects"]


async def createProject(session: AsyncSession, userId: str, name: str):
    project = await projectCore.createProject(session, name=name, userId=userId)
    timeline = await timelineCore.createTimeline(session, projectId=project.id)
    for kind in DEFAULT_TRACK_KINDS:
        await tracksCore.addTrack(session, timeline.id, kind)
    return {"project": project, "timeline": timeline}


async def listProjects(session: AsyncSession, userId: str) -> list[Project]:
    return await projectCore.listProjects(session, userId=userId)


async def getProject(session: AsyncSession, projectId: str, userId: str) -> Project:
    project = await projectCore.getProject(session, projectId=projectId)
    if project is None or project.userId != userId:
        raise ValueError("Project not found")
    return project


async def getTimeline(session: AsyncSession, projectId: str, userId: str) -> TimelineDetail:
    project = await projectCore.getProject(session, projectId=projectId)
    if project is None or project.userId != userId:
        raise ValueError("Project not found")

    timeline = await timelineCore.getTimelineByProjectId(session, projectId=project.id)
    if timeline is None:
        raise ValueError("Timeline not found")

    tracks = await tracksCore.getTracks(session, timeline.id)
    trackDetails = []
    for track in tracks:
        layers = await layersCore.getLayers(session, track.id)
        trackDetails.append(TrackDetail(**track.model_dump(), layers=layers))

    return TimelineDetail(project=project, timeline=timeline, tracks=trackDetails)


async def updateProject(session: AsyncSession, projectId: str, userId: str, name: str) -> Project:
    project = await projectCore.getProject(session, projectId=projectId)
    if project is None or project.userId != userId:
        raise ValueError("Project not found")
    updated = await projectCore.updateProject(session, projectId=projectId, name=name)
    if updated is None:
        raise ValueError("Project not found")
    return updated


async def deleteProject(session: AsyncSession, projectId: str, userId: str) -> bool:
    project = await projectCore.getProject(session, projectId=projectId)
    if project is None or project.userId != userId:
        raise ValueError("Project not found")
    return await projectCore.deleteProject(session, projectId=projectId)
