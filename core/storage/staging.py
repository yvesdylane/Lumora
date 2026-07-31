from __future__ import annotations

from pathlib import Path

from models.asset import Asset
from models.storage import StoragePrefix

from core.storage.backend import getBackend
from core.storage.keys import buildKey, stagingPrefix


def moveToStaging(asset: Asset, runId: str) -> Asset:
    """Server-side copy asset into staging/{runId}/. Returns Asset with updated b2Key."""
    if not asset.b2Key:
        raise ValueError("Asset.b2Key is required to move to staging")

    stagingKey = buildKey(
        StoragePrefix.STAGING,
        runId=runId,
        assetId=asset.id,
        mimeType=asset.mimeType,
    )
    getBackend().copy(asset.b2Key, stagingKey)
    return asset.model_copy(update={"b2Key": stagingKey})


def promoteStagingToFinal(asset: Asset, finalPrefix: str) -> Asset:
    """
    Promote a staged object to a permanent prefix, then delete the staging copy.

    finalPrefix should be e.g. 'generated-audio/{project_id}' or
    'generated-image/{project_id}' (with or without trailing slash).
    """
    if not asset.b2Key:
        raise ValueError("Asset.b2Key is required to promote from staging")
    if not asset.b2Key.startswith(f"{StoragePrefix.STAGING}/"):
        raise ValueError(f"Asset is not in staging: {asset.b2Key}")

    prefix = finalPrefix.strip("/")
    ext = Path(asset.b2Key).suffix or ""
    # finalPrefix already includes project_id segment
    finalKey = f"{prefix}/{asset.id}{ext}"

    backend = getBackend()
    backend.copy(asset.b2Key, finalKey)
    backend.delete(asset.b2Key)
    return asset.model_copy(update={"b2Key": finalKey})


def deleteStaging(runId: str) -> None:
    """Delete all objects under staging/{runId}/."""
    getBackend().delete_prefix(stagingPrefix(runId), dry_run=False)
