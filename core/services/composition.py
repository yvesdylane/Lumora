from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.assets.assets import getMediaInfo
from core.assets.models import AssetRow
from core.storage.b2 import downloadAsset
from core.timeline.models import ProjectRow, TimelineRow, TrackRow
from models.asset import Asset
from models.renderParams import LayerComposition, TimelineComposition, TrackComposition


async def getProjectComposition(
    session: AsyncSession,
    projectId: str,
) -> TimelineComposition:
    result = await session.execute(
        select(TimelineRow)
        .options(
            selectinload(TimelineRow.tracks)
            .selectinload(TrackRow.layers)
        )
        .join(ProjectRow, TimelineRow.project_id == ProjectRow.id)
        .where(ProjectRow.id == uuid.UUID(projectId))
    )
    timelineRow = result.scalar_one_or_none()
    if timelineRow is None:
        return TimelineComposition(tracks=[])

    tracks = []
    for trackRow in sorted(timelineRow.tracks, key=lambda t: t.position):
        layers = []
        for layerRow in sorted(trackRow.layers, key=lambda l: l.position):
            layers.append(
                LayerComposition(
                    layerType=layerRow.layer_type,
                    params=layerRow.params,
                    source=layerRow.source,
                    position=layerRow.position,
                )
            )
        tracks.append(
            TrackComposition(
                kind=trackRow.kind,
                position=trackRow.position,
                layers=layers,
            )
        )

    return TimelineComposition(tracks=tracks)


async def buildAssetRegistry(
    session: AsyncSession,
    projectId: str,
) -> dict[str, Asset]:
    composition = await getProjectComposition(session, projectId)

    assetIds: set[str] = set()
    for track in composition.tracks:
        for layer in track.layers:
            assetId = layer.params.get("assetId")
            if assetId:
                assetIds.add(assetId)

    registry: dict[str, Asset] = {}
    for aid in assetIds:
        asset = await _loadAssetForRender(session, aid)
        if asset is None:
            continue
        registry[aid] = asset

    return registry


async def _loadAssetForRender(session: AsyncSession, assetId: str) -> Asset | None:
    """Resolve a layer assetId to a renderable Asset: load the row, download from B2 if needed."""
    try:
        row = await session.get(AssetRow, uuid.UUID(assetId))
    except (ValueError, TypeError):
        return None
    if row is None:
        return None

    asset = Asset(
        id=str(row.id),
        source=row.source or "upload",
        mimeType=row.mime_type or "application/octet-stream",
        duration=float(row.duration) if row.duration else None,
        b2Key=row.b2_key,
        localPath=row.local_path,
        sha256=row.sha256,
    )

    localMissing = asset.localPath is None or not Path(asset.localPath).exists()
    if localMissing and asset.b2Key:
        try:
            asset = downloadAsset(asset.b2Key, mimeType=asset.mimeType)
            asset = asset.model_copy(update={"id": str(row.id)})
        except Exception:
            return None

    if asset.duration is None:
        try:
            info = getMediaInfo(asset)
            asset.duration = info.duration
        except Exception:
            pass

    return asset
