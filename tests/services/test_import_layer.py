from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.services.import_layer import importAndLayer


@pytest.mark.asyncio
@patch("core.services.import_layer.addLayer", new_callable=AsyncMock)
@patch("core.services.import_layer.importAsset")
async def test_importAndLayer_imports_asset_and_creates_layer(
    mockImportAsset,
    mockAddLayer,
    mockSession,
    fakeLayer,
):
    fakeAsset = MagicMock()
    fakeAsset.id = "asset-123"

    mockImportAsset.return_value = fakeAsset
    mockAddLayer.return_value = fakeLayer

    result = await importAndLayer(
        mockSession,
        localPath="/tmp/video.mp4",
        projectId="proj-1",
        trackId="track-1",
        kind="video",
    )

    mockImportAsset.assert_called_once_with("/tmp/video.mp4", "proj-1", "video")

    mockAddLayer.assert_called_once_with(
        mockSession,
        trackId="track-1",
        layerType="clip",
        params={"assetId": "asset-123", "start": 0.0},
        source="manual",
    )

    assert result == fakeLayer


@pytest.mark.asyncio
@patch("core.services.import_layer.addLayer", new_callable=AsyncMock)
@patch("core.services.import_layer.importAsset")
async def test_importAndLayer_passes_correct_params(
    mockImportAsset,
    mockAddLayer,
    mockSession,
    fakeLayer,
):
    fakeAsset = MagicMock()
    fakeAsset.id = "asset-456"
    mockImportAsset.return_value = fakeAsset
    mockAddLayer.return_value = fakeLayer

    await importAndLayer(
        mockSession,
        localPath="/tmp/audio.mp3",
        projectId="proj-2",
        trackId="track-2",
        kind="audio",
    )

    mockImportAsset.assert_called_once_with("/tmp/audio.mp3", "proj-2", "audio")
    call_kwargs = mockAddLayer.call_args
    assert call_kwargs[1]["params"]["assetId"] == "asset-456"
