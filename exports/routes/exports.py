from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from core.database import getSession
from core.exports import exports as exportsCore
from exports.controllers import exports as exportsController
from exports.schemas import CreateExportRequest, ExportListResponse, ExportResponse

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _exportToResponse(export) -> ExportResponse:
    return ExportResponse(
        id=export.id,
        projectId=export.projectId,
        timelineId=export.timelineId,
        status=export.status,
        outputFormat=export.outputFormat,
        b2Key=export.b2Key,
        error=export.error,
        createdAt=export.createdAt,
        updatedAt=export.updatedAt,
    )


@router.post("", response_model=ExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    data: CreateExportRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    export = await exportsController.createExport(
        session,
        user=user,
        projectId=data.projectId,
        timelineId=data.timelineId,
        outputFormat=data.outputFormat,
    )
    return _exportToResponse(export)


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    export = await exportsController.getExport(session, user=user, exportId=export_id)
    if export is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )
    return _exportToResponse(export)


@router.get("", response_model=ExportListResponse)
async def list_exports(
    projectId: str = Query(...),
    status: str | None = Query(None),
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    exports = await exportsCore.listExports(session, projectId=projectId, status=status)
    return ExportListResponse(exports=[_exportToResponse(e) for e in exports])


@router.websocket("/ws/exports/{export_id}")
async def export_ws(
    ws: WebSocket,
    export_id: str,
):
    await exportsController.wsConnect(export_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await exportsController.wsDisconnect(export_id, ws)
