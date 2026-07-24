from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.services.project import setupProject


@pytest.mark.asyncio
@patch("core.services.project.addTrack", new_callable=AsyncMock)
@patch("core.services.project.createTimeline", new_callable=AsyncMock)
@patch("core.services.project.createProject", new_callable=AsyncMock)
async def test_setupProject_creates_project_timeline_and_tracks(
    mockCreateProject,
    mockCreateTimeline,
    mockAddTrack,
    mockSession,
    fakeProject,
):
    from models.timeline import Timeline

    mockTimeline = Timeline(
        id="tl-123",
        projectId=fakeProject.id,
        createdAt=fakeProject.createdAt,
        updatedAt=fakeProject.updatedAt,
    )

    mockCreateProject.return_value = fakeProject
    mockCreateTimeline.return_value = mockTimeline
    mockAddTrack.return_value = None

    result = await setupProject(mockSession, "My Project", "user-1")

    mockCreateProject.assert_called_once_with(mockSession, "My Project", "user-1")
    mockCreateTimeline.assert_called_once_with(mockSession, fakeProject.id)

    assert mockAddTrack.call_count == 3
    mockAddTrack.assert_any_call(mockSession, mockTimeline.id, "video")
    mockAddTrack.assert_any_call(mockSession, mockTimeline.id, "audio")
    mockAddTrack.assert_any_call(mockSession, mockTimeline.id, "text")

    assert result == fakeProject
    assert result.name == "Test Project"


@pytest.mark.asyncio
@patch("core.services.project.addTrack", new_callable=AsyncMock)
@patch("core.services.project.createTimeline", new_callable=AsyncMock)
@patch("core.services.project.createProject", new_callable=AsyncMock)
async def test_setupProject_returns_project_model(
    mockCreateProject,
    mockCreateTimeline,
    mockAddTrack,
    mockSession,
    fakeProject,
):
    from models.timeline import Timeline

    mockCreateProject.return_value = fakeProject
    mockCreateTimeline.return_value = Timeline(
        id="tl-456",
        projectId=fakeProject.id,
        createdAt=fakeProject.createdAt,
        updatedAt=fakeProject.updatedAt,
    )

    result = await setupProject(mockSession, "Another Project", "user-2")

    assert hasattr(result, "id")
    assert hasattr(result, "name")
    assert hasattr(result, "userId")
