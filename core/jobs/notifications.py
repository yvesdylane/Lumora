from __future__ import annotations

import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)

_connections: dict[str, list[WebSocket]] = defaultdict(list)


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
