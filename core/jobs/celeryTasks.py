from __future__ import annotations

import asyncio
import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from core.jobs.celeryApp import celery
from core.jobs.dispatcher import dispatchJob
from core.jobs.jobs import getJob

import auth.models
import core.assets.models
import core.jobs.models
import core.timeline.models

logger = logging.getLogger(__name__)


def _taskSessionFactory() -> tuple:
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost:5432/lumora")
    engine = create_async_engine(url, poolclass=NullPool)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, factory


@celery.task(name="jobs.run_generation")
def runGenerationJob(jobId: str) -> None:
    """Celery task entrypoint: execute a GenerationJob in the worker process."""
    asyncio.run(_runJobAsync(jobId))


async def _runJobAsync(jobId: str) -> None:
    engine, factory = _taskSessionFactory()
    try:
        async with factory() as session:
            job = await getJob(session, jobId)
            if job is None:
                logger.error(f"Job {jobId} not found")
                return
            await dispatchJob(session, job)
    finally:
        await engine.dispose()
