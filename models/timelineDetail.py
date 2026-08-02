from __future__ import annotations

from pydantic import BaseModel, Field

from models.layer import Layer
from models.project import Project
from models.timeline import Timeline
from models.track import Track


class TrackDetail(Track):
    layers: list[Layer] = Field(default_factory=list)


class TimelineDetail(BaseModel):
    project: Project
    timeline: Timeline
    tracks: list[TrackDetail] = Field(default_factory=list)
