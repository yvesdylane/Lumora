from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict

import redis.asyncio as aioredis
from fastapi import WebSocket

from utils.settings import getSettings

logger = logging.getLogger(__name__)

_connections: dict[str, list[WebSocket]] = defaultdict(list)

_CHANNEL_PREFIX = "lumora:jobs:"

_publishClient: aioredis.Redis | None = None
_subscriberClient: aioredis.Redis | None = None
_subscriberTask: asyncio.Task | None = None
_pubsub: aioredis.client.PubSub | None = None


def _redisClient() -> aioredis.Redis:
    return aioredis.from_url(getSettings().redis_url, decode_responses=True)


async def connect(jobId: str, ws: WebSocket) -> None:
    await ws.accept()
    _connections[jobId].append(ws)
    logger.info(f"WS connected: job={jobId} (total={len(_connections[jobId])})")


async def disconnect(jobId: str, ws: WebSocket) -> None:
    if ws in _connections[jobId]:
        _connections[jobId].remove(ws)
    if not _connections[jobId]:
        del _connections[jobId]
    logger.info(f"WS disconnected: job={jobId}")


async def broadcast(jobId: str, payload: dict) -> None:
    """Publish a job status update to Redis. The API process's subscriber
    forwards it to locally-connected WebSocket clients. Falls back to a direct
    local send if Redis is unreachable (e.g. in-process dispatch)."""
    global _publishClient
    try:
        if _publishClient is None:
            _publishClient = _redisClient()
        await _publishClient.publish(
            f"{_CHANNEL_PREFIX}{jobId}", json.dumps(payload)
        )
    except Exception as e:
        logger.warning(f"redis publish failed for job={jobId}: {e}")
        await _sendLocal(jobId, payload)


async def _sendLocal(jobId: str, payload: dict) -> None:
    if jobId not in _connections:
        return
    dead = []
    for ws in _connections[jobId]:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _connections[jobId].remove(ws)
    if not _connections[jobId]:
        del _connections[jobId]


def getConnections(jobId: str) -> int:
    return len(_connections.get(jobId, []))


async def startSubscriber() -> None:
    """Subscribe to lumora:jobs:* and forward messages to local WebSockets."""
    global _subscriberClient, _subscriberTask, _pubsub
    if _subscriberTask is not None:
        return
    _subscriberClient = _redisClient()
    _pubsub = _subscriberClient.pubsub()
    await _pubsub.psubscribe(f"{_CHANNEL_PREFIX}*")
    logger.info("Redis job subscriber started")
    _subscriberTask = asyncio.create_task(_subscriberLoop())


async def _subscriberLoop() -> None:
    try:
        async for message in _pubsub.listen():
            if message.get("type") != "pmessage":
                continue
            channel = message["channel"]
            jobId = (
                channel[len(_CHANNEL_PREFIX):]
                if channel.startswith(_CHANNEL_PREFIX)
                else channel
            )
            raw = message["data"]
            if not isinstance(raw, str):
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            await _sendLocal(jobId, payload)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.warning(f"subscriber loop stopped: {e}")
    finally:
        if _pubsub is not None:
            await _pubsub.close()


async def stopSubscriber() -> None:
    global _subscriberClient, _subscriberTask
    if _subscriberTask is not None:
        _subscriberTask.cancel()
        try:
            await _subscriberTask
        except asyncio.CancelledError:
            pass
        _subscriberTask = None
    if _subscriberClient is not None:
        await _subscriberClient.aclose()
        _subscriberClient = None
