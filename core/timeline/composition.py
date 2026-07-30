from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.timeline.models import LayerRow, TimelineRow, TrackRow
from models.renderParams import (
    LayerComposition,
    TimelineComposition,
    TrackComposition,
)


async def buildTimelineComposition(
    session: AsyncSession,
    timelineId: str,
) -> TimelineComposition:
    result = await session.execute(
        select(TimelineRow)
        .options(selectinload(TimelineRow.tracks).selectinload(TrackRow.layers))
        .where(TimelineRow.id == uuid.UUID(timelineId))
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise ValueError(f"Timeline not found: {timelineId}")

    tracks = []
    for trackRow in sorted(row.tracks, key=lambda t: t.position):
        layers = [
            LayerComposition(
                layerType=layerRow.layer_type,
                params=dict(layerRow.params) if layerRow.params else {},
                source=layerRow.source,
                position=layerRow.position,
            )
            for layerRow in sorted(trackRow.layers, key=lambda l: l.position)
        ]
        tracks.append(TrackComposition(
            kind=trackRow.kind,
            position=trackRow.position,
            layers=layers,
        ))

    return TimelineComposition(tracks=tracks)
