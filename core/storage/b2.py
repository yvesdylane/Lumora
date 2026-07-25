from __future__ import annotations

import hashlib
from pathlib import Path

from models.asset import Asset
from models.storage import StoragePrefix

from core.storage.backend import get_backend
from core.storage.keys import build_key


def _sha256File(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def uploadAsset(
    asset: Asset,
    *,
    projectId: str,
    prefix: StoragePrefix | str,
    exportId: str | None = None,
) -> Asset:
    if not asset.localPath:
        raise ValueError("Asset.localPath is required for upload")

    path = Path(asset.localPath)
    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {path}")

    sha256 = asset.sha256 or _sha256File(path)

    if prefix == StoragePrefix.RENDERS:
        if not exportId:
            raise ValueError("exportId is required for renders/ uploads")
        key = build_key(
            prefix,
            projectId=projectId,
            exportId=exportId,
        )
    else:
        key = build_key(
            prefix,
            projectId=projectId,
            assetId=asset.id,
            mimeType=asset.mimeType,
        )

    with path.open("rb") as fh:
        get_backend().put(key, fh, content_type=asset.mimeType)

    return asset.model_copy(update={"b2Key": key, "sha256": sha256})


def downloadAsset(b2Key: str, *, mimeType: str = "application/octet-stream") -> Asset:
    backend = get_backend()
    data = backend.get(b2Key)
    from core.storage.cache import writeCacheBytes
    path = writeCacheBytes(b2Key, data, mimeType=mimeType)
    assetId = Path(b2Key).stem
    asset = Asset(
        id=assetId,
        source="upload",
        mimeType=mimeType,
        b2Key=b2Key,
        localPath=str(path),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    from core.storage.cache import ensureLocal
    return ensureLocal(asset)


def getPresignedUrl(b2Key: str, expiresIn: int = 3600) -> str:
    return get_backend().presigned_get_url(b2Key, expires_in=expiresIn)
