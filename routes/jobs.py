from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from controllers import jobs as jobsController
from core.database import getSession
from core.jobs.notifications import connect, disconnect
from models.job import CreateJobRequest, GenerationJob

router = APIRouter(prefix="/api/projects/{projectId}/jobs", tags=["jobs"])


@router.post("/", response_model=GenerationJob, status_code=status.HTTP_201_CREATED)
async def createJob(
    projectId: str,
    data: CreateJobRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    job = await jobsController.createAndDispatchJob(
        session, projectId, str(user.id), data.tier, data.jobType, data.prompt
    )
    return GenerationJob.model_validate(job)


@router.get("/", response_model=list[GenerationJob])
async def listJobs(
    projectId: str,
    status: str | None = Query(None),
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    jobs = await jobsController.listJobs(session, projectId, str(user.id), status)
    return [GenerationJob.model_validate(j) for j in jobs]


@router.get("/{jobId}", response_model=GenerationJob)
async def getJob(
    projectId: str,
    jobId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    job = await jobsController.getJob(session, projectId, jobId, str(user.id))
    return GenerationJob.model_validate(job)


@router.post("/{jobId}/accept", response_model=GenerationJob)
async def acceptJob(
    projectId: str,
    jobId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    job = await jobsController.acceptJob(session, projectId, jobId, str(user.id))
    return GenerationJob.model_validate(job)


@router.post("/{jobId}/retry", response_model=GenerationJob)
async def retryJob(
    projectId: str,
    jobId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    job = await jobsController.retryJob(session, projectId, jobId, str(user.id))
    return GenerationJob.model_validate(job)


@router.delete("/{jobId}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteJob(
    projectId: str,
    jobId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await jobsController.deleteJob(session, projectId, jobId, str(user.id))


@router.websocket("/{jobId}/ws")
async def jobWebSocket(websocket: WebSocket, projectId: str, jobId: str):
    await websocket.accept()
    await connect(jobId, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await disconnect(jobId, websocket)
