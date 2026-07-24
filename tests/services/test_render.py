from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.services.render import renderProject
from models.asset import Asset
from models.renderParams import TimelineComposition, TrackComposition


@pytest.mark.asyncio
@patch("core.services.render.renderTimeline", new_callable=AsyncMock)
@patch("core.services.render.buildAssetRegistry", new_callable=AsyncMock)
@patch("core.services.render.getProjectComposition", new_callable=AsyncMock)
async def test_renderProject_orchestrates_full_pipeline(
    mockGetComposition,
    mockBuildRegistry,
    mockRenderTimeline,
    mockSession,
    fakeAsset,
):
    composition = TimelineComposition(tracks=[])
    mockGetComposition.return_value = composition
    mockBuildRegistry.return_value = {"a1": fakeAsset}
    mockRenderTimeline.return_value = fakeAsset

    result = await renderProject(mockSession, "proj-1")

    mockGetComposition.assert_called_once_with(mockSession, "proj-1")
    mockBuildRegistry.assert_called_once_with(mockSession, "proj-1")
    mockRenderTimeline.assert_called_once()

    call_args = mockRenderTimeline.call_args
    assert call_args[0][0] == composition
    assert call_args[0][1] == {"a1": fakeAsset}

    assert result == fakeAsset


@pytest.mark.asyncio
@patch("core.services.render.renderTimeline", new_callable=AsyncMock)
@patch("core.services.render.buildAssetRegistry", new_callable=AsyncMock)
@patch("core.services.render.getProjectComposition", new_callable=AsyncMock)
async def test_renderProject_passes_composition_to_renderer(
    mockGetComposition,
    mockBuildRegistry,
    mockRenderTimeline,
    mockSession,
):
    composition = TimelineComposition(
        tracks=[TrackComposition(kind="video", position=0)]
    )
    mockGetComposition.return_value = composition
    mockBuildRegistry.return_value = {}
    mockRenderTimeline.return_value = Asset(
        id="rendered-1", source="upload", mimeType="video/mp4"
    )

    await renderProject(mockSession, "proj-1")

    mockRenderTimeline.assert_called_once_with(composition, {})
