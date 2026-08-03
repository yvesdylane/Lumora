from __future__ import annotations

import asyncio
import json
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
from core.jobs.dispatcher import dispatchJob
from core.jobs.jobs import createJob as createJobCore
from core.jobs.jobs import getJob
from core.timeline.layers import addLayer
from models.asset import Asset
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
    payload = _parsePayload(job.prompt)
    genJobType = (expected or payload).get("jobType", job.jobType)

    if genJobType not in _TIER1_FNS:
        raise ValueError(
            f"Agentic generation not supported for job type: {genJobType}"
        )

    maxAttempts = int(payload.get("maxAttempts", job.maxAttempts))
    innerArgs = _buildTier1Args(genJobType, payload)

    async def generateOne(**kwargs: object) -> Asset:
        innerJob = await createJobCore(
            session,
            projectId=job.projectId,
            tier=1,
            jobType=genJobType,
            prompt=json.dumps(kwargs),
        )
        await dispatchJob(session, innerJob)
        completed = await _waitForJob(session, innerJob.id)
        if (
            completed is None
            or completed.status != "completed"
            or not completed.result
        ):
            detail = completed.error if completed else "inner job lost"
            raise RuntimeError(f"Generation attempt failed: {detail}")
        assetData = completed.result.get("asset", {})
        return Asset(
            id=assetData.get("id", ""),
            source=assetData.get("source", "ai"),
            mimeType=assetData.get("mimeType", "application/octet-stream"),
            duration=assetData.get("duration"),
            b2Key=assetData.get("b2Key"),
            localPath=assetData.get("localPath"),
        )

    result = await runAgenticLoop(
        generateFn=generateOne,
        jobArgs=innerArgs,
        expected=expected,
        maxAttempts=maxAttempts,
    )

    if result.decision == "store" and result.asset:
        layerType = "clip" if genJobType in _CLIP_TYPES else "audio"
        params = {"assetId": result.asset.id, "start": 0.0}
        if layerType == "audio":
            params["volume"] = 0.8

        layer = await addLayer(
            session,
            trackId=trackId,
            layerType=layerType,
            params=params,
            source="genblaze_generated",
        )
        result.layerId = layer.id

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


def _buildTier1Args(jobType: str, payload: dict) -> dict:
    args: dict = {}

    if jobType == "voiceover":
        args["script"] = payload.get("script", payload.get("prompt", ""))
        args["voiceConfig"] = payload.get("voiceConfig", {})

    elif jobType == "music":
        args["prompt"] = payload.get("prompt", "")
        args["duration"] = payload.get("duration", 30.0)

    elif jobType == "image":
        args["prompt"] = payload.get("prompt", "")
        if payload.get("size"):
            args["size"] = payload["size"]

    elif jobType == "video":
        args["prompt"] = payload.get("prompt", "")
        args["duration"] = payload.get("duration", 5.0)

    if payload.get("model"):
        args["model"] = payload["model"]

    return args


def _parsePayload(prompt: str) -> dict:
    try:
        return json.loads(prompt)
    except (json.JSONDecodeError, TypeError):
        return {}
