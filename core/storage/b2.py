from __future__ import annotations

import hashlib
from pathlib import Path

from models.asset import Asset
from models.storage import StoragePrefix

from core.storage.backend import getBackend
from core.storage.cache import ensureLocal, writeCacheBytes
from core.storage.keys import buildKey


def _sha256_file(path: Path) -> str:
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
    """Upload a local asset to B2 under the given Lumora prefix. Returns updated Asset."""
    if not asset.localPath:
        raise ValueError("Asset.localPath is required for upload")

    path = Path(asset.localPath)
    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {path}")

    sha256 = asset.sha256 or _sha256_file(path)

    if str(prefix) == StoragePrefix.RENDERS:
        if not exportId:
            raise ValueError("exportId is required for renders/ uploads")
        key = buildKey(
            prefix,
            projectId=projectId,
            exportId=exportId,
        )
    else:
        key = buildKey(
            prefix,
            projectId=projectId,
            assetId=asset.id,
            mimeType=asset.mimeType,
        )

    with path.open("rb") as fh:
        getBackend().put(key, fh, content_type=asset.mimeType)

    return asset.model_copy(update={"b2Key": key, "sha256": sha256})


def downloadAsset(b2Key: str, *, mimeType: str = "application/octet-stream") -> Asset:
    """Download a B2 object into the local cache and return an Asset with localPath set."""
    backend = getBackend()
    data = backend.get(b2Key)
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
    return ensureLocal(asset)


def getPresignedUrl(b2Key: str, expiresIn: int = 3600) -> str:
    """Return a short-lived presigned GET URL for a B2 object."""
    return getBackend().presigned_get_url(b2Key, expires_in=expiresIn)
