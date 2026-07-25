from __future__ import annotations

import hashlib
from pathlib import Path

from models.asset import Asset
from utils.mime import extension_for_mime
from utils.settings import get_settings


def cachePathFor(b2Key: str, *, mimeType: str | None = None) -> Path:
    settings = get_settings()
    digest = hashlib.sha256(b2Key.encode("utf-8")).hexdigest()
    ext = extension_for_mime(mimeType) if mimeType else Path(b2Key).suffix
    return settings.lumora_cache_dir / f"{digest}{ext}"


def writeCacheBytes(
    b2Key: str,
    data: bytes,
    *,
    mimeType: str | None = None,
) -> Path:
    path = cachePathFor(b2Key, mimeType=mimeType)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def ensureLocal(asset: Asset) -> Asset:
    if asset.localPath and Path(asset.localPath).exists():
        return asset

    if not asset.b2Key:
        raise ValueError("Asset has no localPath or b2Key")

    cached = cachePathFor(asset.b2Key, mimeType=asset.mimeType)
    if cached.exists():
        return asset.model_copy(update={"localPath": str(cached)})

    from core.storage.backend import get_backend

    data = get_backend().get(asset.b2Key)
    path = writeCacheBytes(asset.b2Key, data, mimeType=asset.mimeType)
    return asset.model_copy(update={"localPath": str(path)})
