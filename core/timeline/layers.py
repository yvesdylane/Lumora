from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.assets.models import AssetRow
from core.timeline.models import LayerRow
from models.layer import Layer


async def _enrichAssetDuration(
    session: AsyncSession, layerType: str, params: dict
) -> None:
    if layerType not in ("clip", "audio"):
        return
    assetId = params.get("assetId")
    if not assetId or params.get("duration") is not None:
        return
    try:
        row = await session.get(AssetRow, uuid.UUID(str(assetId)))
    except ValueError:
        return
    if row and row.duration is not None:
        params["duration"] = float(row.duration)


async def addLayer(
    session: AsyncSession,
    trackId: str,
    layerType: str,
    params: dict,
    source: str = "manual",
) -> Layer:
    params = dict(params)
    await _enrichAssetDuration(session, layerType, params)
    result = await session.execute(
        select(LayerRow.position)
        .where(LayerRow.track_id == uuid.UUID(trackId))
        .order_by(LayerRow.position.desc())
        .limit(1)
    )
    lastPos = result.scalar_one_or_none()
    nextPos = (lastPos or -1) + 1

    row = LayerRow(
        track_id=uuid.UUID(trackId),
        layer_type=layerType,
        params=params,
        source=source,
        position=nextPos,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def getLayers(session: AsyncSession, trackId: str) -> list[Layer]:
    result = await session.execute(
        select(LayerRow)
        .where(LayerRow.track_id == uuid.UUID(trackId))
        .order_by(LayerRow.position)
    )
    return [_toModel(r) for r in result.scalars().all()]


async def updateLayer(session: AsyncSession, layerId: str, params: dict) -> Layer | None:
    row = await session.get(LayerRow, uuid.UUID(layerId))
    if not row:
        return None
    params = dict(params)
    await _enrichAssetDuration(session, row.layer_type, params)
    row.params = params
    await session.commit()
    await session.refresh(row)
    return _toModel(row)


async def deleteLayer(session: AsyncSession, layerId: str) -> bool:
    row = await session.get(LayerRow, uuid.UUID(layerId))
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


def _toModel(row: LayerRow) -> Layer:
    return Layer(
        id=str(row.id),
        trackId=str(row.track_id),
        layerType=row.layer_type,
        params=row.params,
        source=row.source,
        position=row.position,
        createdAt=row.created_at,
        updatedAt=row.updated_at,
    )
