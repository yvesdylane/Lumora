from __future__ import annotations

_EXT_MAP: dict[str, str] = {
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/ogg": ".ogg",
    "audio/flac": ".flac",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "video/mp4": ".mp4",
    "video/quicktime": ".mov",
    "video/webm": ".webm",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "application/json": ".json",
    "text/plain": ".txt",
}

_MIME_BY_EXT: dict[str, str] = {v: k for k, v in _EXT_MAP.items()}


def extension_for_mime(mime_type: str | None) -> str:
    if not mime_type:
        return ""
    return _EXT_MAP.get(mime_type, "")


def mime_for_extension(ext: str) -> str:
    if not ext:
        return "application/octet-stream"
    if not ext.startswith("."):
        ext = f".{ext}"
    return _MIME_BY_EXT.get(ext, "application/octet-stream")
