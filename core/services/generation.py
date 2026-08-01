from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.ai.agentic import AgenticResult, runAgenticLoop
from core.ai.tier1 import (
    generateImage,
    generateMusic,
    generateVideo,
    generateVoiceover,
)
from core.jobs.celeryTasks import runGenerationJob
from core.jobs.jobs import getJob
from core.timeline.layers import addLayer
from models.job import GenerationJob
from models.layer import Layer

logger = logging.getLogger(__name__)

_TIER1_FNS = {
    "voiceover": generateVoiceover,
    "music": generateMusic,
    "image": generateImage,
    "video": generateVideo,
}

_CLIP_TYPES = {"image", "video"}
_AUDIO_TYPES = {"voiceover", "music"}


async def generateAndApply(
    session: AsyncSession,
    job: GenerationJob,
    trackId: str,
) -> Layer | None:
    runGenerationJob.apply_async(args=[job.id])
    completed = await _waitForJob(session, job.id)

    if completed is None or completed.status != "completed" or not completed.result:
        logger.warning(f"Job {job.id} did not complete successfully: status={completed.status if completed else 'unknown'}")
        return None

    layerType, params = _resultToLayer(job.jobType, completed.result)

    if layerType is None:
        return None

    return await addLayer(
        session,
        trackId=trackId,
        layerType=layerType,
        params=params,
        source="genblaze_generated",
    )


async def _waitForJob(
    session: AsyncSession,
    jobId: str,
    timeout: float = 300.0,
    interval: float = 1.0,
) -> GenerationJob | None:
    """Poll the DB until a job leaves the running/pending state."""
    elapsed = 0.0
    while elapsed < timeout:
        job = await getJob(session, jobId)
        if job is not None and job.status not in {"pending", "running"}:
            return job
        await asyncio.sleep(interval)
        elapsed += interval
    return await getJob(session, jobId)


async def runAgenticGeneration(
    session: AsyncSession,
    job: GenerationJob,
    trackId: str,
    expected: dict | None = None,
) -> AgenticResult:
    genFn = _TIER1_FNS.get(job.jobType)
    if genFn is None:
        raise ValueError(f"Agentic generation not supported for job type: {job.jobType}")

    jobArgs = _buildJobArgs(job)

    result = await runAgenticLoop(
        generateFn=genFn,
        jobArgs=jobArgs,
        expected=expected,
        maxAttempts=job.maxAttempts,
    )

    if result.decision == "store" and result.asset:
        layerType = "clip" if job.jobType in _CLIP_TYPES else "audio"
        params = {"assetId": result.asset.id, "start": 0.0}
        if layerType == "audio":
            params["volume"] = 0.8

        await addLayer(
            session,
            trackId=trackId,
            layerType=layerType,
            params=params,
            source="genblaze_generated",
        )

    return result


def _resultToLayer(jobType: str, result: dict) -> tuple[str | None, dict]:
    if jobType in _CLIP_TYPES:
        assetData = result.get("asset", {})
        assetId = assetData.get("id", "")
        return "clip", {"assetId": assetId, "start": 0.0}

    if jobType in _AUDIO_TYPES:
        assetData = result.get("asset", {})
        assetId = assetData.get("id", "")
        return "audio", {"assetId": assetId, "volume": 0.8, "startTime": 0.0}

    if jobType == "caption":
        return "text", result.get("result", {})

    if jobType == "transition":
        return "transition", result.get("result", {})

    return None, {}


def _buildJobArgs(job: GenerationJob) -> dict:
    import json

    try:
        payload = json.loads(job.prompt)
    except (json.JSONDecodeError, TypeError):
        payload = {}

    args: dict = {}

    if job.jobType == "voiceover":
        args["script"] = payload.get("script", job.prompt)
        args["voiceConfig"] = payload.get("voiceConfig", {})
        if "model" in payload:
            args["model"] = payload["model"]

    elif job.jobType == "music":
        args["prompt"] = job.prompt
        args["duration"] = payload.get("duration", 30.0)
        if "model" in payload:
            args["model"] = payload["model"]

    elif job.jobType == "image":
        args["prompt"] = job.prompt
        if "model" in payload:
            args["model"] = payload["model"]
        if "size" in payload:
            args["size"] = payload["size"]

    elif job.jobType == "video":
        args["prompt"] = job.prompt
        if "model" in payload:
            args["model"] = payload["model"]
        args["duration"] = payload.get("duration", 5.0)

    return args
