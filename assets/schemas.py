from __future__ import annotations

from pydantic import BaseModel


class ImportRequest(BaseModel):
    projectId: str
    kind: str


class ImportResponse(BaseModel):
    id: str
    source: str
    mimeType: str
    duration: float | None = None
    b2Key: str | None = None
    localPath: str | None = None
    sha256: str | None = None
    manifestRef: str | None = None
    tags: list[str] = []


class AssetListResponse(BaseModel):
    assets: list[ImportResponse]


class TagUpdateRequest(BaseModel):
    tags: list[str]


class PresignedUrlResponse(BaseModel):
    url: str
