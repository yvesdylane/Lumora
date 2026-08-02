from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from core.assets.assets import getMediaInfo, importAsset, persistStorageMetadata
from core.storage import b2 as b2Storage
from core.timeline.layers import addLayer
from models.layer import Layer
from models.storage import StoragePrefix


async def importAndLayer(
    session: AsyncSession,
    *,
    userId: str,
    localPath: str,
    projectId: str,
    trackId: str,
    kind: str,
) -> Layer:
    asset = await importAsset(
        session,
        userId=uuid.UUID(userId),
        projectId=uuid.UUID(projectId),
        localPath=localPath,
        kind=kind,
    )

    asset = b2Storage.uploadAsset(asset, projectId=projectId, prefix=StoragePrefix.UPLOADS)

    duration = None
    mediaInfo = getMediaInfo(asset)
    if mediaInfo.duration:
        duration = mediaInfo.duration

    persisted = await persistStorageMetadata(
        session,
        assetId=uuid.UUID(asset.id),
        b2Key=asset.b2Key,
        sha256=asset.sha256,
        duration=duration,
    )
    if persisted is not None:
        asset = persisted

    layer = await addLayer(
        session,
        trackId=trackId,
        layerType="clip",
        params={"assetId": asset.id, "start": 0.0},
        source="manual",
    )

    return layer
