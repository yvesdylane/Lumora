from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Asset(BaseModel):
    id: str
    source: Literal["upload", "ai"]
    mimeType: str
    duration: float | None = None
    b2Key: str | None = None
    localPath: str | None = None
    sha256: str | None = None
    manifestRef: str | None = None
    tags: list[str] = []


class MediaInfo(BaseModel):
    duration: float | None = None
    fps: float | None = None
    resolution: tuple[int, int] | None = None
    codec: str | None = None
    hasAudio: bool = False
