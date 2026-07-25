from __future__ import annotations

from pydantic import BaseModel


class VoiceoverRequest(BaseModel):
    projectId: str
    script: str
    voiceConfig: dict = {}
    model: str | None = None


class MusicRequest(BaseModel):
    projectId: str
    prompt: str
    duration: float = 30.0
    model: str | None = None


class ImageRequest(BaseModel):
    projectId: str
    prompt: str
    model: str | None = None
    size: str | None = None


class VideoRequest(BaseModel):
    projectId: str
    prompt: str
    model: str | None = None
    duration: float = 5.0
    aspectRatio: str = "16:9"
    quality: str = "720p"
