from __future__ import annotations

from pydantic import BaseModel


class VoiceoverRequest(BaseModel):
    projectId: str
    script: str
    voiceConfig: dict | None = None


class MusicRequest(BaseModel):
    projectId: str
    prompt: str
    duration: float = 30.0


class ImageRequest(BaseModel):
    projectId: str
    prompt: str
    size: str | None = None


class AIJobResponse(BaseModel):
    jobId: str
    status: str
