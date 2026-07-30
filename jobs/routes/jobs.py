from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from core.database import getSession
from jobs.controllers import jobs as jobsController
from jobs.schemas import CreateJobRequest, JobListResponse, JobResponse

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _jobToResponse(job) -> JobResponse:
    return JobResponse(
        id=job.id,
        projectId=job.projectId,
        tier=job.tier,
        jobType=job.jobType,
        prompt=job.prompt,
        status=job.status,
        result=job.result,
        error=job.error,
        attempts=job.attempts,
        maxAttempts=job.maxAttempts,
        createdAt=job.createdAt,
        updatedAt=job.updatedAt,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def createJob(
    data: CreateJobRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    job = await jobsController.createJob(
        session,
        user=user,
        projectId=data.projectId,
        tier=data.tier,
        jobType=data.jobType,
        prompt=data.prompt,
    )
    return _jobToResponse(job)


@router.get("/{job_id}", response_model=JobResponse)
async def getJob(
    job_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    job = await jobsController.getJob(session, user=user, jobId=job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return _jobToResponse(job)
