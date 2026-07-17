from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Asset(BaseModel):
    id: str
    source: Literal["upload", "ai"]
    mime_type: str
    duration: float | None = None
    b2_key: str | None = None
    local_path: str | None = None
    sha256: str | None = None
    manifest_ref: str | None = None
    tags: list[str] = []


class MediaInfo(BaseModel):
    duration: float | None = None
    fps: float | None = None
    resolution: tuple[int, int] | None = None
    codec: str | None = None
    has_audio: bool = False
