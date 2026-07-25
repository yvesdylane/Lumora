from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from models.asset import Asset
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


async def dispatchJobBackground(jobId: str) -> None:
    """Run a job dispatch in the background with a fresh DB session."""
    from core.database import asyncSession
    from core.jobs.jobs import getJob

    async with asyncSession() as session:
        job = await getJob(session, jobId)
        if not job:
            logger.error(f"Background dispatch: job {jobId} not found")
            return
        await dispatchJob(session, job)


def _scheduleBackground(jobId: str) -> None:
    """Fire-and-forget background dispatch via asyncio task."""
    asyncio.create_task(_runBackgroundWrapper(jobId))


async def _runBackgroundWrapper(jobId: str) -> None:
    try:
        await dispatchJobBackground(jobId)
    except Exception as e:
        logger.error(f"Background dispatch failed for job {jobId}: {e}")


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
    from core.ai.agentic import runAgenticLoop

    payload = _parsePayload(job.prompt)

    genFns = {
        "voiceover": generateVoiceover,
        "music": generateMusic,
        "image": generateImage,
        "video": generateVideo,
    }

    genFn = genFns.get(job.jobType)
    if not genFn:
        raise ValueError(f"Unknown tier1 job type: {job.jobType}")

    jobArgs, expected = _buildGenArgs(job.jobType, payload, job.prompt)

    async def onAttempt(attempt: int, run: Any) -> None:
        await broadcast(job.id, {
            "status": "running",
            "jobId": job.id,
            "attempt": attempt,
            "score": run.score,
            "decision": run.decision,
            "checks": [
                {"name": c.name, "passed": c.passed, "score": c.score, "detail": c.detail}
                for c in run.checks
            ],
        })

    agenticResult = await runAgenticLoop(
        generateFn=genFn,
        jobArgs=jobArgs,
        expected=expected,
        maxAttempts=job.maxAttempts,
        onAttempt=onAttempt,
    )

    if agenticResult.asset:
        return {
            "tier": 1,
            "jobType": job.jobType,
            "asset": {
                "id": agenticResult.asset.id,
                "mimeType": agenticResult.asset.mimeType,
                "source": agenticResult.asset.source,
                "duration": agenticResult.asset.duration,
            },
            "decision": agenticResult.decision,
            "attempts": agenticResult.attempts,
        }

    raise RuntimeError(f"Agentic loop exhausted: {agenticResult.error or 'no asset produced'}")


def _buildGenArgs(
    jobType: str, payload: dict, prompt: str
) -> tuple[dict, dict | None]:
    if jobType == "voiceover":
        return {
            "script": payload.get("script", prompt),
            "voiceConfig": payload.get("voiceConfig", {}),
            "model": payload.get("model"),
        }, {"script": payload.get("script", prompt)}

    if jobType == "music":
        return {
            "prompt": prompt,
            "duration": payload.get("duration", 30.0),
            "model": payload.get("model"),
        }, None

    if jobType == "image":
        return {
            "prompt": prompt,
            "model": payload.get("model"),
            "size": payload.get("size"),
        }, None

    if jobType == "video":
        return {
            "prompt": prompt,
            "model": payload.get("model"),
            "duration": payload.get("duration", 5.0),
            "aspectRatio": payload.get("aspectRatio", "16:9"),
            "quality": payload.get("quality", "720p"),
        }, None

    raise ValueError(f"Unknown job type: {jobType}")


def _parsePayload(prompt: str) -> dict:
    try:
        return json.loads(prompt)
    except (json.JSONDecodeError, TypeError):
        return {}
