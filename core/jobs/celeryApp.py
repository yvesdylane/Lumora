from __future__ import annotations

from celery import Celery

from utils.settings import getSettings

celery = Celery(
    "lumora",
    broker=getSettings().redis_url,
    include=["core.jobs.celeryTasks"],
)

celery.conf.task_acks_late = True
celery.conf.worker_prefetch_multiplier = 1
