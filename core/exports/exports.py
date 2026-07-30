from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exports.models import ExportRow
from models.export import Export


async def createExport(
    session: AsyncSession,
    projectId: str,
    timelineId: str,
    outputFormat: str = "mp4",
) -> Export:
    row = ExportRow(
        project_id=uuid.UUID(projectId),
        timeline_id=uuid.UUID(timelineId),
        output_format=outputFormat,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def getExport(
    session: AsyncSession,
    exportId: str,
) -> Export | None:
    row = await session.get(ExportRow, uuid.UUID(exportId))
    return _toModel(row) if row else None


async def listExports(
    session: AsyncSession,
    projectId: str,
    status: str | None = None,
) -> list[Export]:
    query = select(ExportRow).where(
        ExportRow.project_id == uuid.UUID(projectId)
    )
    if status:
        query = query.where(ExportRow.status == status)
    query = query.order_by(ExportRow.created_at.desc())
    result = await session.execute(query)
    return [_toModel(r) for r in result.scalars().all()]


async def updateExportStatus(
    session: AsyncSession,
    exportId: str,
    status: str,
    b2Key: str | None = None,
    error: str | None = None,
) -> Export | None:
    row = await session.get(ExportRow, uuid.UUID(exportId))
    if not row:
        return None
    row.status = status
    if b2Key is not None:
        row.b2_key = b2Key
    if error is not None:
        row.error = error
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


def _toModel(row: ExportRow) -> Export:
    return Export(
        id=str(row.id),
        projectId=str(row.project_id),
        timelineId=str(row.timeline_id),
        status=row.status,
        outputFormat=row.output_format,
        b2Key=row.b2_key,
        error=row.error,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )
