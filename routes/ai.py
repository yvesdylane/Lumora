from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from controllers.ownership import verifyProjectOwnership
from core.database import getSession
from core.jobs.dispatcher import _scheduleBackground
from core.jobs.jobs import createJob
from models.ai import VoiceoverRequest, MusicRequest, ImageRequest, VideoRequest
from models.job import GenerationJob

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/voiceover", response_model=GenerationJob, status_code=status.HTTP_202_ACCEPTED)
async def createVoiceover(
    data: VoiceoverRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await verifyProjectOwnership(session, data.projectId, str(user.id))
    import json
    payload = json.dumps({
        "script": data.script,
        "voiceConfig": data.voiceConfig,
        "model": data.model,
    })
    job = await createJob(session, data.projectId, 1, "voiceover", payload)
    _scheduleBackground(job.id)
    return GenerationJob.model_validate(job)


@router.post("/music", response_model=GenerationJob, status_code=status.HTTP_202_ACCEPTED)
async def createMusic(
    data: MusicRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await verifyProjectOwnership(session, data.projectId, str(user.id))
    import json
    payload = json.dumps({
        "prompt": data.prompt,
        "duration": data.duration,
        "model": data.model,
    })
    job = await createJob(session, data.projectId, 1, "music", payload)
    _scheduleBackground(job.id)
    return GenerationJob.model_validate(job)


@router.post("/image", response_model=GenerationJob, status_code=status.HTTP_202_ACCEPTED)
async def createImage(
    data: ImageRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await verifyProjectOwnership(session, data.projectId, str(user.id))
    import json
    payload = json.dumps({
        "prompt": data.prompt,
        "model": data.model,
        "size": data.size,
    })
    job = await createJob(session, data.projectId, 1, "image", payload)
    _scheduleBackground(job.id)
    return GenerationJob.model_validate(job)


@router.post("/video", response_model=GenerationJob, status_code=status.HTTP_202_ACCEPTED)
async def createVideo(
    data: VideoRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await verifyProjectOwnership(session, data.projectId, str(user.id))
    import json
    payload = json.dumps({
        "prompt": data.prompt,
        "model": data.model,
        "duration": data.duration,
        "aspectRatio": data.aspectRatio,
        "quality": data.quality,
    })
    job = await createJob(session, data.projectId, 1, "video", payload)
    _scheduleBackground(job.id)
    return GenerationJob.model_validate(job)
