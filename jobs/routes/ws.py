from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.jobs.notifications import connect, disconnect

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/jobs/{job_id}")
async def jobWebsocket(job_id: str, ws: WebSocket):
    await connect(job_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await disconnect(job_id, ws)
    except Exception as e:
        logger.warning(f"WS error job={job_id}: {e}")
        await disconnect(job_id, ws)
