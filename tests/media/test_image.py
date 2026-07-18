# tests/media/test_image.py

import pytest
from pathlib import Path

from core.media.image import (
    addImageOverlay,
    extractFrame,
    generateThumbnail,
    _resolvePosition,
)
from models.asset import Asset


# ── helpers ──────────────────────────────────────────────────────────────────

def makeVideo(localPath: str, duration: float = 5.0) -> Asset:
    return Asset(
        id="test-video",
        source="upload",
        mimeType="video/mp4",
        duration=duration,
        localPath=localPath,
    )


def makeImage(localPath: str) -> Asset:
    return Asset(
        id="test-image",
        source="upload",
        mimeType="image/png",
        localPath=localPath,
    )


# ── unit tests (no ffmpeg needed) ────────────────────────────────────────────

class TestResolvePosition:
    def test_numericPosition(self):
        x, y = _resolvePosition({"x": 100, "y": 200}, Path("."), Path("."))
        assert x == "100"
        assert y == "200"

    def test_centerX(self):
        x, y = _resolvePosition({"x": "center", "y": 50}, Path("."), Path("."))
        assert "main_w" in x
        assert y == "50"

    def test_centerY(self):
        x, y = _resolvePosition({"x": 100, "y": "center"}, Path("."), Path("."))
        assert x == "100"
        assert "main_h" in y

    def test_bothCentered(self):
        x, y = _resolvePosition({"x": "center", "y": "center"}, Path("."), Path("."))
        assert "main_w" in x
        assert "main_h" in y

    def test_defaultPosition(self):
        x, y = _resolvePosition({}, Path("."), Path("."))
        assert x == "0"
        assert y == "0"


# ── integration tests (require ffmpeg + fixture files) ───────────────────────

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(
    not (FIXTURES / "sample.mp4").exists(),
    reason="fixture files not present"
)
class TestGenerateThumbnail:
    def test_defaultTimestamp(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        result = generateThumbnail(video)

        assert result.localPath is not None
        assert Path(result.localPath).exists()
        assert result.mimeType == "image/jpeg"
        assert Path(result.localPath).suffix == ".jpg"

    def test_customTimestamp(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        result = generateThumbnail(video, timestamp=2.5)

        assert Path(result.localPath).exists()
        assert result.mimeType == "image/jpeg"

    def test_zeroTimestamp(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        result = generateThumbnail(video, timestamp=0.0)

        assert Path(result.localPath).exists()

    def test_missingLocalPathRaises(self):
        badAsset = Asset(id="x", source="upload", mimeType="video/mp4")
        with pytest.raises(ValueError, match="neither localPath nor b2Key"):
            generateThumbnail(badAsset)


@pytest.mark.skipif(
    not (FIXTURES / "sample.mp4").exists(),
    reason="fixture files not present"
)
class TestExtractFrame:
    def test_pngFormat(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        result = extractFrame(video, timestamp=1.0, format="png")

        assert result.localPath is not None
        assert Path(result.localPath).exists()
        assert result.mimeType == "image/png"
        assert Path(result.localPath).suffix == ".png"

    def test_jpgFormat(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        result = extractFrame(video, timestamp=1.0, format="jpg")

        assert Path(result.localPath).exists()
        assert result.mimeType == "image/jpeg"
        assert Path(result.localPath).suffix == ".jpg"

    def test_differentTimestampsProduceDifferentFiles(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        r1 = extractFrame(video, timestamp=0.5)
        r2 = extractFrame(video, timestamp=3.0)

        assert r1.localPath != r2.localPath
        assert Path(r1.localPath).exists()
        assert Path(r2.localPath).exists()

    def test_missingLocalPathRaises(self):
        badAsset = Asset(id="x", source="upload", mimeType="video/mp4")
        with pytest.raises(ValueError, match="neither localPath nor b2Key"):
            extractFrame(badAsset, timestamp=1.0)


@pytest.mark.skipif(
    not (FIXTURES / "sample.mp4").exists() or not (FIXTURES / "test_image.png").exists(),
    reason="fixture files not present"
)
class TestAddImageOverlay:
    def test_overlayProducesOutputFile(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        image = makeImage(str(FIXTURES / "test_image.png"))

        result = addImageOverlay(
            video, image,
            position={"x": 10, "y": 10},
            startTime=0.0,
            duration=2.0,
        )

        assert result.localPath is not None
        assert Path(result.localPath).exists()
        assert result.mimeType == "video/mp4"

    def test_overlayWithCenterPosition(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        image = makeImage(str(FIXTURES / "test_image.png"))

        result = addImageOverlay(
            video, image,
            position={"x": "center", "y": "center"},
            startTime=1.0,
            duration=3.0,
        )

        assert Path(result.localPath).exists()

    def test_overlayWithLateStart(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        image = makeImage(str(FIXTURES / "test_image.png"))

        result = addImageOverlay(
            video, image,
            position={"x": 0, "y": 0},
            startTime=3.0,
            duration=2.0,
        )

        assert Path(result.localPath).exists()

    def test_missingVideoRaises(self):
        badAsset = Asset(id="x", source="upload", mimeType="video/mp4")
        image = makeImage(str(FIXTURES / "test_image.png"))

        with pytest.raises(ValueError, match="neither localPath nor b2Key"):
            addImageOverlay(badAsset, image, {"x": 0, "y": 0}, 0.0, 1.0)

    def test_missingImageRaises(self):
        video = makeVideo(str(FIXTURES / "sample.mp4"))
        badAsset = Asset(id="x", source="upload", mimeType="image/png")

        with pytest.raises(ValueError, match="neither localPath nor b2Key"):
            addImageOverlay(video, badAsset, {"x": 0, "y": 0}, 0.0, 1.0)
