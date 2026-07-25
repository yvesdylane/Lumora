from __future__ import annotations

from pathlib import Path

from models.asset import Asset
from models.storage import StoragePrefix

from core.storage.backend import get_backend
from core.storage.keys import build_key, stagingPrefix


def moveToStaging(asset: Asset, runId: str) -> Asset:
    if not asset.b2Key:
        raise ValueError("Asset.b2Key is required to move to staging")

    stagingKey = build_key(
        StoragePrefix.STAGING,
        runId=runId,
        assetId=asset.id,
        mimeType=asset.mimeType,
    )
    get_backend().copy(asset.b2Key, stagingKey)
    return asset.model_copy(update={"b2Key": stagingKey})


def promoteStagingToFinal(asset: Asset, finalPrefix: str) -> Asset:
    if not asset.b2Key:
        raise ValueError("Asset.b2Key is required to promote from staging")
    if not asset.b2Key.startswith(f"{StoragePrefix.STAGING.value}/"):
        raise ValueError(f"Asset is not in staging: {asset.b2Key}")

    prefix = finalPrefix.strip("/")
    ext = Path(asset.b2Key).suffix or ""
    finalKey = f"{prefix}/{asset.id}{ext}"

    backend = get_backend()
    backend.copy(asset.b2Key, finalKey)
    backend.delete(asset.b2Key)
    return asset.model_copy(update={"b2Key": finalKey})


def deleteStaging(runId: str) -> None:
    get_backend().delete_prefix(stagingPrefix(runId), dry_run=False)
