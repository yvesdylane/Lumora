from __future__ import annotations

from pathlib import Path

_EXT_MAP: dict[str, str] = {
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/x-msvideo": ".avi",
    "video/webm": ".webm",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/aac": ".aac",
    "audio/flac": ".flac",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "application/json": ".json",
}


def extension_for_mime(mime_type: str) -> str:
    return _EXT_MAP.get(mime_type, Path(mime_type.split("/")[-1]).suffix or "")
