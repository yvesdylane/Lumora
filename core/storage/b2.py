from __future__ import annotations

import hashlib
from pathlib import Path

from models.asset import Asset
from models.storage import StoragePrefix

from core.storage.backend import get_backend
from core.storage.cache import ensure_local, write_cache_bytes
from core.storage.keys import build_key


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload_asset(
    asset: Asset,
    *,
    project_id: str,
    prefix: StoragePrefix | str,
    export_id: str | None = None,
) -> Asset:
    """Upload a local asset to B2 under the given Lumora prefix. Returns updated Asset."""
    if not asset.local_path:
        raise ValueError("Asset.local_path is required for upload")

    path = Path(asset.local_path)
    if not path.exists():
        raise FileNotFoundError(f"Local file not found: {path}")

    sha256 = asset.sha256 or _sha256_file(path)

    if str(prefix) == StoragePrefix.RENDERS:
        if not export_id:
            raise ValueError("export_id is required for renders/ uploads")
        key = build_key(
            prefix,
            project_id=project_id,
            export_id=export_id,
        )
    else:
        key = build_key(
            prefix,
            project_id=project_id,
            asset_id=asset.id,
            mime_type=asset.mime_type,
        )

    with path.open("rb") as fh:
        get_backend().put(key, fh, content_type=asset.mime_type)

    return asset.model_copy(update={"b2_key": key, "sha256": sha256})


def download_asset(b2_key: str, *, mime_type: str = "application/octet-stream") -> Asset:
    """Download a B2 object into the local cache and return an Asset with local_path set."""
    backend = get_backend()
    data = backend.get(b2_key)
    path = write_cache_bytes(b2_key, data, mime_type=mime_type)
    asset_id = Path(b2_key).stem
    asset = Asset(
        id=asset_id,
        source="upload",
        mime_type=mime_type,
        b2_key=b2_key,
        local_path=str(path),
        sha256=hashlib.sha256(data).hexdigest(),
    )
    return ensure_local(asset)


def get_presigned_url(b2_key: str, expires_in: int = 3600) -> str:
    """Return a short-lived presigned GET URL for a B2 object."""
    return get_backend().presigned_get_url(b2_key, expires_in=expires_in)
