from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from models.asset import Asset, MediaInfo


def import_asset(local_path: str, project_id: str, kind: str) -> Asset:
    path = Path(local_path)
    if not path.exists():
        raise FileNotFoundError(f"Asset not found: {local_path}")

    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    return Asset(
        id=str(uuid.uuid4()),
        source="upload",
        mime_type=_guess_mime(path, kind),
        local_path=str(path.resolve()),
        sha256=sha256,
    )


def get_media_info(asset: Asset) -> MediaInfo:
    if asset.local_path is None:
        return MediaInfo()

    path = Path(asset.local_path)
    if not path.exists():
        return MediaInfo()

    # TODO: probe with ffprobe when media module is built
    return MediaInfo()


def search_assets(query: str, tags: list[str] | None = None) -> list[Asset]:
    # TODO: implement with DB-backed asset index
    return []


def tag_asset(asset: Asset, tags: list[str]) -> Asset:
    existing = set(asset.tags)
    existing.update(tags)
    return asset.model_copy(update={"tags": sorted(existing)})


def _guess_mime(path: Path, kind: str) -> str:
    mapping = {
        "video": "video/mp4",
        "audio": "audio/mpeg",
        "image": "image/png",
    }
    return mapping.get(kind, "application/octet-stream")
