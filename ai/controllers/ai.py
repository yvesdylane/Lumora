from __future__ import annotations

import json
from typing import Literal

from auth.models import UserRow
from core.jobs.celeryTasks import runGenerationJob
from core.jobs.jobs import createJob as createJobCore
from models.job import GenerationJob
from sqlalchemy.ext.asyncio import AsyncSession


async def generateVoiceover(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    script: str,
    voiceConfig: dict | None = None,
) -> GenerationJob:
    payload = json.dumps({
        "script": script,
        "voiceConfig": voiceConfig or {},
    })
    job = await createJobCore(
        session,
        projectId=projectId,
        tier=1,
        jobType="voiceover",
        prompt=payload,
    )
    _enqueue(job.id)
    return job


async def generateMusic(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    prompt: str,
    duration: float = 30.0,
) -> GenerationJob:
    payload = json.dumps({"duration": duration})
    job = await createJobCore(
        session,
        projectId=projectId,
        tier=1,
        jobType="music",
        prompt=prompt,
    )
    _enqueue(job.id)
    return job


async def generateImage(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    prompt: str,
    size: str | None = None,
) -> GenerationJob:
    payload = json.dumps({"size": size} if size else {})
    job = await createJobCore(
        session,
        projectId=projectId,
        tier=1,
        jobType="image",
        prompt=prompt,
    )
    _enqueue(job.id)
    return job


def _enqueue(jobId: str) -> None:
    runGenerationJob.apply_async(args=[jobId])
