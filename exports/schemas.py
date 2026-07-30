from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CreateExportRequest(BaseModel):
    projectId: str
    timelineId: str
    outputFormat: str = "mp4"


class ExportResponse(BaseModel):
    id: str
    projectId: str
    timelineId: str
    status: str
    outputFormat: str
    b2Key: str | None = None
    error: str | None = None
    createdAt: datetime
    updatedAt: datetime


class ExportListResponse(BaseModel):
    exports: list[ExportResponse]
