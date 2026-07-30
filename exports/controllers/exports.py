from __future__ import annotations

import asyncio

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from auth.models import UserRow
from core.exports import exports as exportsCore
from core.jobs import notifications
from core.renderer.dispatch import dispatchRender
from models.export import Export


async def createExport(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    timelineId: str,
    outputFormat: str = "mp4",
) -> Export:
    export = await exportsCore.createExport(
        session,
        projectId=projectId,
        timelineId=timelineId,
        outputFormat=outputFormat,
    )

    asyncio.create_task(
        dispatchRender(
            exportId=export.id,
            projectId=projectId,
            timelineId=timelineId,
            outputFormat=outputFormat,
        )
    )

    return export


async def getExport(
    session: AsyncSession,
    *,
    user: UserRow,
    exportId: str,
) -> Export | None:
    return await exportsCore.getExport(session, exportId)


async def wsConnect(exportId: str, ws: WebSocket) -> None:
    await notifications.connect(exportId, ws)


async def wsDisconnect(exportId: str, ws: WebSocket) -> None:
    await notifications.disconnect(exportId, ws)
