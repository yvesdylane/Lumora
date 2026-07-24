from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.assets.assets import getMediaInfo
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
        asset = Asset(
            id=aid,
            source="upload",
            mimeType="video/mp4",
        )
        try:
            info = getMediaInfo(asset)
            asset.duration = info.duration
        except Exception:
            pass
        registry[aid] = asset

    return registry
