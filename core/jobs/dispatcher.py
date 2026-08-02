from __future__ import annotations

import json
import logging
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from models.job import GenerationJob
from core.jobs.jobs import updateJobStatus
from core.jobs.notifications import broadcast

logger = logging.getLogger(__name__)

TIER0_JOB_TYPES = {"caption", "transition", "cut_points", "motion_spec"}
TIER1_JOB_TYPES = {"voiceover", "music", "image", "video"}


async def dispatchJob(
    session: AsyncSession,
    job: GenerationJob,
) -> GenerationJob:
    await broadcast(job.id, {"status": "running", "jobId": job.id})

    updated = await updateJobStatus(session, job.id, "running")
    if not updated:
        return job

    try:
        if job.tier == 0:
            result = await _dispatchTier0(job)
        elif job.tier == 1:
            result = await _dispatchTier1(job)
        elif job.tier == 2:
            result = await _dispatchTier2(session, job)
        else:
            raise ValueError(f"Unknown tier: {job.tier}")

        completed = await updateJobStatus(
            session, job.id, "completed", result=result
        )
        await broadcast(job.id, {
            "status": "completed",
            "jobId": job.id,
            "result": result,
        })
        return completed or job

    except Exception as e:
        logger.error(f"Job {job.id} failed: {e}")
        failed = await updateJobStatus(
            session, job.id, "failed", error=str(e)
        )
        await broadcast(job.id, {
            "status": "failed",
            "jobId": job.id,
            "error": str(e),
        })
        return failed or job


async def _dispatchTier0(job: GenerationJob) -> dict:
    from core.ai.llmClient import MockLLMClient
    from core.ai.tier0 import (
        generateCaptions,
        suggestTransition,
        suggestCutPoints,
        generateMotionSpec,
    )

    client = MockLLMClient()
    payload = _parsePayload(job.prompt)

    if job.jobType == "caption":
        result = await generateCaptions(
            client,
            transcript=payload.get("transcript", ""),
            wordTimings=payload.get("wordTimings", []),
        )
    elif job.jobType == "transition":
        result = await suggestTransition(
            client,
            clipAMeta=payload.get("clipA", {}),
            clipBMeta=payload.get("clipB", {}),
        )
    elif job.jobType == "cut_points":
        result = await suggestCutPoints(
            client,
            timeline=payload.get("timeline", {}),
            targetDuration=payload.get("targetDuration", 30.0),
        )
    elif job.jobType == "motion_spec":
        result = await generateMotionSpec(
            client,
            style=payload.get("style", "cinematic"),
            layerType=payload.get("layerType", "video"),
        )
    else:
        raise ValueError(f"Unknown tier0 job type: {job.jobType}")

    return {"tier": 0, "jobType": job.jobType, "result": result}


async def _dispatchTier1(job: GenerationJob) -> dict:
    from core.ai.tier1 import generateVoiceover, generateMusic, generateImage, generateVideo

    payload = _parsePayload(job.prompt)

    if job.jobType == "voiceover":
        asset = await generateVoiceover(
            script=payload.get("script", job.prompt),
            voiceConfig=payload.get("voiceConfig", {}),
            model=payload.get("model"),
        )
    elif job.jobType == "music":
        asset = await generateMusic(
            prompt=job.prompt,
            duration=payload.get("duration", 30.0),
            model=payload.get("model"),
        )
    elif job.jobType == "image":
        asset = await generateImage(
            prompt=job.prompt,
            model=payload.get("model"),
            size=payload.get("size"),
        )
    elif job.jobType == "video":
        asset = await generateVideo(
            prompt=job.prompt,
            model=payload.get("model"),
            duration=payload.get("duration", 5.0),
        )
    else:
        raise ValueError(f"Unknown tier1 job type: {job.jobType}")

    return {
        "tier": 1,
        "jobType": job.jobType,
        "asset": {
            "id": asset.id,
            "mimeType": asset.mimeType,
            "source": asset.source,
            "duration": asset.duration,
        },
    }


def _parsePayload(prompt: str) -> dict:
    try:
        return json.loads(prompt)
    except (json.JSONDecodeError, TypeError):
        return {}


async def _dispatchTier2(session: AsyncSession, job: GenerationJob) -> dict:
    import uuid

    from core.assets.assets import persistGeneratedAsset
    from core.services.render import renderProject
    from core.storage.b2 import uploadAsset
    from core.timeline.projects import getProject
    from models.storage import StoragePrefix

    payload = _parsePayload(job.prompt)
    outputFormat = payload.get("outputFormat", "mp4")

    asset = await renderProject(
        session,
        job.projectId,
        outputFormat=outputFormat,
    )

    uploaded = uploadAsset(
        asset,
        projectId=job.projectId,
        prefix=StoragePrefix.RENDERS,
        exportId=job.id,
    )

    project = await getProject(session, job.projectId)
    if project is None:
        raise ValueError(f"Project not found: {job.projectId}")

    persisted = await persistGeneratedAsset(
        session,
        userId=uuid.UUID(project.userId),
        projectId=uuid.UUID(job.projectId),
        asset=uploaded,
        source="ai",
    )

    return {
        "tier": 2,
        "jobType": job.jobType,
        "asset": {
            "id": persisted.id,
            "mimeType": persisted.mimeType,
            "source": persisted.source,
            "duration": persisted.duration,
            "b2Key": persisted.b2Key,
        },
    }
