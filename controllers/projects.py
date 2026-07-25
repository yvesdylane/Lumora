from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.timeline import projects as projectCore
from core.timeline import timeline as timelineCore
from models.project import Project


async def createProject(session: AsyncSession, userId: str, name: str):
    project = await projectCore.createProject(session, name=name, userId=userId)
    timeline = await timelineCore.createTimeline(session, projectId=project.id)
    return {"project": project, "timeline": timeline}


async def listProjects(session: AsyncSession, userId: str) -> list[Project]:
    return await projectCore.listProjects(session, userId=userId)


async def getProject(session: AsyncSession, projectId: str, userId: str) -> Project:
    project = await projectCore.getProject(session, projectId=projectId)
    if project is None or project.userId != userId:
        raise ValueError("Project not found")
    return project


async def getTimeline(session: AsyncSession, projectId: str, userId: str):
    project = await projectCore.getProject(session, projectId=projectId)
    if project is None or project.userId != userId:
        raise ValueError("Project not found")
    return await timelineCore.getTimelineByProjectId(session, projectId=project.id)


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
