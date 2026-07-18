from __future__ import annotations

import hashlib
import json
import subprocess
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

    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return MediaInfo()

    data = json.loads(result.stdout)
    videoStream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    hasAudio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))

    duration = float(data.get("format", {}).get("duration", 0))
    fps = None
    resolution = None
    codec = None

    if videoStream:
        codec = videoStream.get("codec_name")
        w = videoStream.get("width")
        h = videoStream.get("height")
        if w and h:
            resolution = (w, h)
        rawFps = videoStream.get("r_frame_rate", "")
        if "/" in rawFps:
            num, den = rawFps.split("/")
            if float(den) != 0:
                fps = round(float(num) / float(den), 2)
        elif rawFps:
            fps = float(rawFps)

    return MediaInfo(
        duration=duration,
        fps=fps,
        resolution=resolution,
        codec=codec,
        hasAudio=hasAudio,
    )


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
