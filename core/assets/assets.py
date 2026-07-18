from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

from models.asset import Asset, MediaInfo


def importAsset(localPath: str, projectId: str, kind: str) -> Asset:
    path = Path(localPath)
    if not path.exists():
        raise FileNotFoundError(f"Asset not found: {localPath}")

    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()

    return Asset(
        id=str(uuid.uuid4()),
        source="upload",
        mimeType=_guessMime(path, kind),
        localPath=str(path.resolve()),
        sha256=sha256,
    )


def getMediaInfo(asset: Asset) -> MediaInfo:
    if asset.localPath is None:
        return MediaInfo()

    path = Path(asset.localPath)
    if not path.exists():
        return MediaInfo()

    # TODO: probe with ffprobe when media module is built
    return MediaInfo()


def searchAssets(query: str, tags: list[str] | None = None) -> list[Asset]:
    # TODO: implement with DB-backed asset index
    return []


def tagAsset(asset: Asset, tags: list[str]) -> Asset:
    existing = set(asset.tags)
    existing.update(tags)
    return asset.model_copy(update={"tags": sorted(existing)})


def _guessMime(path: Path, kind: str) -> str:
    mapping = {
        "video": "video/mp4",
        "audio": "audio/mpeg",
        "image": "image/png",
    }
    return mapping.get(kind, "application/octet-stream")
