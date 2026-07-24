from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.jobs.models import JobRow
from models.job import GenerationJob


async def createJob(
    session: AsyncSession,
    projectId: str,
    tier: int,
    jobType: str,
    prompt: str = "",
) -> GenerationJob:
    row = JobRow(
        project_id=uuid.UUID(projectId),
        tier=tier,
        job_type=jobType,
        prompt=prompt,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def getJob(session: AsyncSession, jobId: str) -> GenerationJob | None:
    row = await session.get(JobRow, uuid.UUID(jobId))
    return _toModel(row) if row else None


async def listJobs(
    session: AsyncSession,
    projectId: str,
    status: str | None = None,
) -> list[GenerationJob]:
    query = select(JobRow).where(
        JobRow.project_id == uuid.UUID(projectId)
    )
    if status:
        query = query.where(JobRow.status == status)
    query = query.order_by(JobRow.created_at.desc())
    result = await session.execute(query)
    return [_toModel(r) for r in result.scalars().all()]


async def updateJobStatus(
    session: AsyncSession,
    jobId: str,
    status: str,
    result: dict | None = None,
    error: str | None = None,
) -> GenerationJob | None:
    row = await session.get(JobRow, uuid.UUID(jobId))
    if not row:
        return None
    row.status = status
    if result is not None:
        row.result = result
    if error is not None:
        row.error = error
    if status == "running":
        row.attempts += 1
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def deleteJob(session: AsyncSession, jobId: str) -> bool:
    row = await session.get(JobRow, uuid.UUID(jobId))
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


def _toModel(row: JobRow) -> GenerationJob:
    return GenerationJob(
        id=str(row.id),
        projectId=str(row.project_id),
        tier=row.tier,
        jobType=row.job_type,
        prompt=row.prompt,
        status=row.status,
        result=row.result,
        error=row.error,
        attempts=row.attempts,
        maxAttempts=row.max_attempts,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )
