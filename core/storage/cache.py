from __future__ import annotations

import hashlib
from pathlib import Path

from models.asset import Asset
from utils.mime import extension_for_mime
from utils.settings import get_settings


def cache_path_for(b2_key: str, *, mime_type: str | None = None) -> Path:
    """Deterministic local cache path for a B2 object key."""
    settings = get_settings()
    digest = hashlib.sha256(b2_key.encode("utf-8")).hexdigest()
    ext = extension_for_mime(mime_type) if mime_type else Path(b2_key).suffix
    return settings.lumora_cache_dir / f"{digest}{ext}"


def write_cache_bytes(
    b2_key: str,
    data: bytes,
    *,
    mime_type: str | None = None,
) -> Path:
    """Write downloaded bytes into the local cache and return the path."""
    path = cache_path_for(b2_key, mime_type=mime_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def ensure_local(asset: Asset) -> Asset:
    """
    Ensure asset.local_path points at a readable file.

    Cache hit / miss:
      local_path exists → return
      cache hit by b2_key → return with local_path
      else download from B2 → write cache → return
    """
    if asset.local_path and Path(asset.local_path).exists():
        return asset

    if not asset.b2_key:
        raise ValueError("Asset has no local_path or b2_key")

    cached = cache_path_for(asset.b2_key, mime_type=asset.mime_type)
    if cached.exists():
        return asset.model_copy(update={"local_path": str(cached)})

    # Import here to avoid circular import with b2.download_asset → cache
    from core.storage.backend import get_backend

    data = get_backend().get(asset.b2_key)
    path = write_cache_bytes(asset.b2_key, data, mime_type=asset.mime_type)
    return asset.model_copy(update={"local_path": str(path)})
