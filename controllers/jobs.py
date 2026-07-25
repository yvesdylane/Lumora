from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from controllers.ownership import verifyProjectOwnership
from core.jobs import jobs as jobsCore
from core.jobs.dispatcher import dispatchJob
from models.job import GenerationJob


async def createAndDispatchJob(
    session: AsyncSession,
    projectId: str,
    userId: str,
    tier: int,
    jobType: str,
    prompt: str,
) -> GenerationJob:
    await verifyProjectOwnership(session, projectId, userId)
    job = await jobsCore.createJob(session, projectId, tier, jobType, prompt)
    return await dispatchJob(session, job)


async def getJob(
    session: AsyncSession,
    projectId: str,
    jobId: str,
    userId: str,
) -> GenerationJob:
    await verifyProjectOwnership(session, projectId, userId)
    job = await jobsCore.getJob(session, jobId)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


async def listJobs(
    session: AsyncSession,
    projectId: str,
    userId: str,
    statusFilter: str | None = None,
) -> list[GenerationJob]:
    await verifyProjectOwnership(session, projectId, userId)
    return await jobsCore.listJobs(session, projectId, statusFilter)


async def deleteJob(
    session: AsyncSession,
    projectId: str,
    jobId: str,
    userId: str,
) -> None:
    await verifyProjectOwnership(session, projectId, userId)
    deleted = await jobsCore.deleteJob(session, jobId)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
