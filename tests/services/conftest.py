from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.asset import Asset
from models.job import GenerationJob
from models.layer import Layer
from models.project import Project
from models.track import Track


@pytest.fixture
def mockSession():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def fakeProject():
    return Project(
        id=str(uuid.uuid4()),
        name="Test Project",
        userId="00000000-0000-0000-0000-000000000001",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def fakeTrack():
    return Track(
        id=str(uuid.uuid4()),
        timelineId=str(uuid.uuid4()),
        kind="video",
        position=0,
        createdAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def fakeLayer():
    return Layer(
        id=str(uuid.uuid4()),
        trackId=str(uuid.uuid4()),
        layerType="clip",
        params={"assetId": str(uuid.uuid4()), "start": 0.0},
        source="manual",
        position=0,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )


@pytest.fixture
def fakeAsset():
    return Asset(
        id=str(uuid.uuid4()),
        source="upload",
        mimeType="video/mp4",
        localPath="/tmp/test.mp4",
        duration=10.0,
    )


@pytest.fixture
def fakeJob():
    return GenerationJob(
        id=str(uuid.uuid4()),
        projectId=str(uuid.uuid4()),
        tier=1,
        jobType="voiceover",
        prompt="Hello world",
        status="pending",
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
    )
