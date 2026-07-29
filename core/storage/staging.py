from __future__ import annotations

from pathlib import Path

from models.asset import Asset
from models.storage import StoragePrefix

from core.storage.backend import get_backend
from core.storage.keys import build_key, staging_prefix


def move_to_staging(asset: Asset, run_id: str) -> Asset:
    """Server-side copy asset into staging/{run_id}/. Returns Asset with updated b2Key."""
    if not asset.b2Key:
        raise ValueError("Asset.b2Key is required to move to staging")

    staging_key = build_key(
        StoragePrefix.STAGING,
        run_id=run_id,
        asset_id=asset.id,
        mime_type=asset.mimeType,
    )
    get_backend().copy(asset.b2Key, staging_key)
    return asset.model_copy(update={"b2Key": staging_key})


def promote_staging_to_final(asset: Asset, final_prefix: str) -> Asset:
    """
    Promote a staged object to a permanent prefix, then delete the staging copy.

    final_prefix should be e.g. 'generated-audio/{project_id}' or
    'generated-image/{project_id}' (with or without trailing slash).
    """
    if not asset.b2Key:
        raise ValueError("Asset.b2Key is required to promote from staging")
    if not asset.b2Key.startswith(f"{StoragePrefix.STAGING}/"):
        raise ValueError(f"Asset is not in staging: {asset.b2Key}")

    prefix = final_prefix.strip("/")
    ext = Path(asset.b2Key).suffix or ""
    # final_prefix already includes project_id segment
    final_key = f"{prefix}/{asset.id}{ext}"

    backend = get_backend()
    backend.copy(asset.b2Key, final_key)
    backend.delete(asset.b2Key)
    return asset.model_copy(update={"b2Key": final_key})


def delete_staging(run_id: str) -> None:
    """Delete all objects under staging/{run_id}/."""
    get_backend().delete_prefix(staging_prefix(run_id), dry_run=False)
