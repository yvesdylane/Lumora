from __future__ import annotations

from auth.models import UserRow
from core.jobs import jobs as jobsCore
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
    return await jobsCore.createJob(
        session,
        projectId=projectId,
        tier=tier,
        jobType=jobType,
        prompt=prompt,
    )


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
