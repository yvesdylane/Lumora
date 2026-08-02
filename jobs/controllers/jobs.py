from __future__ import annotations

import json

from auth.models import UserRow
from core.jobs import jobs as jobsCore
from core.jobs.celeryTasks import runGenerationJob
from models.job import GenerationJob
from sqlalchemy.ext.asyncio import AsyncSession


async def createJob(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    tier: int,
    jobType: str,
    prompt: str = "",
) -> GenerationJob:
    job = await jobsCore.createJob(
        session,
        projectId=projectId,
        tier=tier,
        jobType=jobType,
        prompt=prompt,
    )
    runGenerationJob.apply_async(args=[job.id])
    return job


async def createRenderJob(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    outputFormat: str = "mp4",
) -> GenerationJob:
    from core.timeline.projects import getProject

    project = await getProject(session, projectId)
    if project is None or project.userId != str(user.id):
        raise ValueError("Project not found")

    payload = json.dumps({"outputFormat": outputFormat})
    job = await jobsCore.createJob(
        session,
        projectId=projectId,
        tier=2,
        jobType="render",
        prompt=payload,
    )
    runGenerationJob.apply_async(args=[job.id])
    return job


async def getJob(
    session: AsyncSession,
    *,
    user: UserRow,
    jobId: str,
) -> GenerationJob | None:
    job = await jobsCore.getJob(session, jobId)
    if job is None:
        return None
    # Ensure user owns the project this job belongs to
    from core.timeline.projects import getProject

    project = await getProject(session, job.projectId)
    if project is None or project.userId != str(user.id):
        return None
    return job
