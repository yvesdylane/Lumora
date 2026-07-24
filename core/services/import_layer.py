from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.assets.assets import importAsset
from core.timeline.layers import addLayer
from models.layer import Layer


async def importAndLayer(
    session: AsyncSession,
    localPath: str,
    projectId: str,
    trackId: str,
    kind: str,
) -> Layer:
    asset = importAsset(localPath, projectId, kind)

    layer = await addLayer(
        session,
        trackId=trackId,
        layerType="clip",
        params={"assetId": asset.id, "start": 0.0},
        source="manual",
    )

    return layer
