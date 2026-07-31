from __future__ import annotations

import hashlib
from pathlib import Path

from models.asset import Asset
from utils.mime import extensionForMime
from utils.settings import getSettings


def cachePathFor(b2Key: str, *, mimeType: str | None = None) -> Path:
    """Deterministic local cache path for a B2 object key."""
    settings = getSettings()
    digest = hashlib.sha256(b2Key.encode("utf-8")).hexdigest()
    ext = extensionForMime(mimeType) if mimeType else Path(b2Key).suffix
    return settings.lumora_cache_dir / f"{digest}{ext}"


def writeCacheBytes(
    b2Key: str,
    data: bytes,
    *,
    mimeType: str | None = None,
) -> Path:
    """Write downloaded bytes into the local cache and return the path."""
    path = cachePathFor(b2Key, mimeType=mimeType)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def ensureLocal(asset: Asset) -> Asset:
    """
    Ensure asset.localPath points at a readable file.

    Cache hit / miss:
      localPath exists -> return
      cache hit by b2Key -> return with localPath
      else download from B2 -> write cache -> return
    """
    if asset.localPath and Path(asset.localPath).exists():
        return asset

    if not asset.b2Key:
        raise ValueError("Asset has no localPath or b2Key")

    cached = cachePathFor(asset.b2Key, mimeType=asset.mimeType)
    if cached.exists():
        return asset.model_copy(update={"localPath": str(cached)})

    # Import here to avoid circular import with b2.downloadAsset -> cache
    from core.storage.backend import getBackend

    data = getBackend().get(asset.b2Key)
    path = writeCacheBytes(asset.b2Key, data, mimeType=asset.mimeType)
    return asset.model_copy(update={"localPath": str(path)})
