from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from core.services.composition import buildAssetRegistry, getProjectComposition
from models.renderParams import (
    LayerComposition,
    TimelineComposition,
    TrackComposition,
)


@pytest.mark.asyncio
@patch("core.services.composition.getMediaInfo")
@patch("core.services.composition.getProjectComposition", new_callable=AsyncMock)
async def test_buildAssetRegistry_collects_asset_ids(
    mockGetComposition,
    mockGetMediaInfo,
    mockSession,
):
    composition = TimelineComposition(
        tracks=[
            TrackComposition(
                kind="video",
                layers=[
                    LayerComposition(layerType="clip", params={"assetId": "a1", "start": 0.0}),
                    LayerComposition(layerType="clip", params={"assetId": "a2", "start": 5.0}),
                ],
            ),
            TrackComposition(
                kind="audio",
                layers=[
                    LayerComposition(layerType="audio", params={"assetId": "a1", "volume": 0.8}),
                ],
            ),
        ]
    )
    mockGetComposition.return_value = composition

    from models.asset import MediaInfo

    mockGetMediaInfo.return_value = MediaInfo(duration=10.0)

    registry = await buildAssetRegistry(mockSession, "proj-1")

    assert "a1" in registry
    assert "a2" in registry
    assert len(registry) == 2

    assert registry["a1"].id == "a1"
    assert registry["a1"].duration == 10.0


@pytest.mark.asyncio
@patch("core.services.composition.getMediaInfo")
@patch("core.services.composition.getProjectComposition", new_callable=AsyncMock)
async def test_buildAssetRegistry_handles_empty_composition(
    mockGetComposition,
    mockGetMediaInfo,
    mockSession,
):
    mockGetComposition.return_value = TimelineComposition(tracks=[])

    registry = await buildAssetRegistry(mockSession, "proj-1")

    assert registry == {}
    mockGetMediaInfo.assert_not_called()


@pytest.mark.asyncio
@patch("core.services.composition.getMediaInfo")
@patch("core.services.composition.getProjectComposition", new_callable=AsyncMock)
async def test_buildAssetRegistry_handles_media_info_failure(
    mockGetComposition,
    mockGetMediaInfo,
    mockSession,
):
    composition = TimelineComposition(
        tracks=[
            TrackComposition(
                kind="video",
                layers=[
                    LayerComposition(layerType="clip", params={"assetId": "a1", "start": 0.0}),
                ],
            ),
        ]
    )
    mockGetComposition.return_value = composition
    mockGetMediaInfo.side_effect = RuntimeError("ffprobe failed")

    registry = await buildAssetRegistry(mockSession, "proj-1")

    assert "a1" in registry
    assert registry["a1"].duration is None
