# tests/media/test_audio.py

import pytest
from pathlib import Path
from core.media.audio import mixAudioLayer, _buildVolumeFilter
from models.asset import Asset


# ── helpers ──────────────────────────────────────────────────────────────────

def makeAsset(localPath: str, duration: float = 10.0) -> Asset:
    return Asset(
        id="test-id",
        source="upload",
        mimeType="video/mp4",
        duration=duration,
        b2Key=None,
        localPath=localPath,
        sha256=None,
        manifestRef=None,
    )


# ── unit tests (no ffmpeg needed) ────────────────────────────────────────────

class TestBuildVolumeFilter:
    def test_emptyEnvelopeReturnsFullVolume(self):
        result = _buildVolumeFilter([])
        assert result == "volume=1.0"

    def test_singleKeyframeReturnsStaticVolume(self):
        result = _buildVolumeFilter([{"time": 0.0, "volume": 0.5}])
        assert "volume=0.5" in result

    def test_multipleKeyframesReturnsDynamicFilter(self):
        envelope = [{"time": 0.0, "volume": 0.0}, {"time": 2.0, "volume": 1.0}]
        result = _buildVolumeFilter(envelope)
        assert "eval=frame" in result

    def test_keyframesAreSortedByTime(self):
        envelope = [{"time": 2.0, "volume": 1.0}, {"time": 0.0, "volume": 0.0}]
        result = _buildVolumeFilter(envelope)
        # Should not raise and should produce a valid filter
        assert "volume" in result


# ── integration tests (require ffmpeg + real media files) ─────────────────────

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(
    not (FIXTURES / "sample.mp4").exists(),
    reason="fixture files not present"
)
class TestMixAudioLayer:
    def test_mixProducesOutputFile(self):
        video = makeAsset(str(FIXTURES / "sample.mp4"), duration=5.0)
        audio = makeAsset(str(FIXTURES / "sample.mp3"), duration=3.0)

        result = mixAudioLayer(video, audio, [], startTime=0.0)

        assert result.localPath is not None
        assert Path(result.localPath).exists()
        assert result.mimeType == "video/mp4"

    def test_mixWithStartTimeOffset(self):
        video = makeAsset(str(FIXTURES / "sample.mp4"), duration=5.0)
        audio = makeAsset(str(FIXTURES / "sample.mp3"), duration=3.0)

        result = mixAudioLayer(video, audio, [], startTime=1.5)

        assert Path(result.localPath).exists()

    def test_mixWithVolumeEnvelope(self):
        video = makeAsset(str(FIXTURES / "sample.mp4"), duration=5.0)
        audio = makeAsset(str(FIXTURES / "sample.mp3"), duration=3.0)
        envelope = [{"time": 0.0, "volume": 0.0}, {"time": 2.0, "volume": 1.0}]

        result = mixAudioLayer(video, audio, envelope, startTime=0.0)

        assert Path(result.localPath).exists()

    def test_missingLocalPathAndB2KeyRaises(self):
        badAsset = Asset(id="x", source="upload", mimeType="video/mp4", duration=5.0)
        audio = makeAsset(str(FIXTURES / "sample.mp3"))

        with pytest.raises(ValueError, match="neither localPath nor b2Key"):
            mixAudioLayer(badAsset, audio, [], startTime=0.0)