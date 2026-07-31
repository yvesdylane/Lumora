from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ai.controllers import ai as aiController
from ai.schemas import AIJobResponse, ImageRequest, MusicRequest, VoiceoverRequest
from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from core.database import getSession

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/voiceover", response_model=AIJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generateVoiceover(
    data: VoiceoverRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    job = await aiController.generateVoiceover(
        session,
        user=user,
        projectId=data.projectId,
        script=data.script,
        voiceConfig=data.voiceConfig,
    )
    return AIJobResponse(jobId=job.id, status=job.status)


@router.post("/music", response_model=AIJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generateMusic(
    data: MusicRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    job = await aiController.generateMusic(
        session,
        user=user,
        projectId=data.projectId,
        prompt=data.prompt,
        duration=data.duration,
    )
    return AIJobResponse(jobId=job.id, status=job.status)


@router.post("/image", response_model=AIJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generateImage(
    data: ImageRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    job = await aiController.generateImage(
        session,
        user=user,
        projectId=data.projectId,
        prompt=data.prompt,
        size=data.size,
    )
    return AIJobResponse(jobId=job.id, status=job.status)
