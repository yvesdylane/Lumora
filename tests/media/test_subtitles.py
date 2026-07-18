# tests/media/test_subtitles.py

import pytest
from pathlib import Path

from core.media.subtitles import (
    addSubtitles,
    _buildAssFile,
    _buildKaraokeText,
    _groupWordsIntoLines,
    _secondsToAssTime,
)
from models.asset import Asset
from models.subtitle import SubtitleParams, WordTiming


# ── helpers ──────────────────────────────────────────────────────────────────

def makeAsset(localPath: str, duration: float = 10.0) -> Asset:
    return Asset(
        id="test-id",
        source="upload",
        mimeType="video/mp4",
        duration=duration,
        localPath=localPath,
    )


def makeWords(*tuples: tuple[str, float, float]) -> list[WordTiming]:
    return [WordTiming(word=w, start=s, end=e) for w, s, e in tuples]


# ── unit tests (no ffmpeg needed) ────────────────────────────────────────────

class TestSecondsToAssTime:
    def test_zero(self):
        assert _secondsToAssTime(0.0) == "0:00:00.00"

    def test_simple_seconds(self):
        assert _secondsToAssTime(65.5) == "0:01:05.50"

    def test_over_one_hour(self):
        assert _secondsToAssTime(3661.25) == "1:01:01.25"

    def test_subsecond(self):
        assert _secondsToAssTime(0.75) == "0:00:00.75"


class TestGroupWordsIntoLines:
    def test_emptyWordsReturnsEmpty(self):
        assert _groupWordsIntoLines([], 5) == []

    def test_singleWord(self):
        words = makeWords(("hello", 0.0, 0.5))
        result = _groupWordsIntoLines(words, 5)
        assert len(result) == 1
        assert result[0][0].word == "hello"

    def test_splitsOnMaxWordsPerLine(self):
        words = makeWords(
            ("a", 0.0, 0.3),
            ("b", 0.3, 0.6),
            ("c", 0.6, 0.9),
            ("d", 0.9, 1.2),
        )
        result = _groupWordsIntoLines(words, 2)
        assert len(result) == 2
        assert [w.word for w in result[0]] == ["a", "b"]
        assert [w.word for w in result[1]] == ["c", "d"]

    def test_remainderGroupedCorrectly(self):
        words = makeWords(
            ("a", 0.0, 0.3),
            ("b", 0.3, 0.6),
            ("c", 0.6, 0.9),
        )
        result = _groupWordsIntoLines(words, 2)
        assert len(result) == 2
        assert len(result[1]) == 1


class TestBuildKaraokeText:
    def test_singleWord(self):
        words = makeWords(("hello", 0.0, 0.5))
        result = _buildKaraokeText(words)
        assert result == "{\\kf50}hello"

    def test_multipleWords(self):
        words = makeWords(
            ("hello", 0.0, 0.5),
            ("world", 0.5, 1.3),
        )
        result = _buildKaraokeText(words)
        assert result == "{\\kf50}hello {\\kf80}world"

    def test_durationInCentiseconds(self):
        words = makeWords(("test", 1.0, 2.25))
        result = _buildKaraokeText(words)
        assert "{\\kf125}" in result


class TestBuildAssFile:
    def test_containsScriptInfo(self):
        params = SubtitleParams(words=makeWords(("hi", 0.0, 0.5)))
        result = _buildAssFile(params)
        assert "[Script Info]" in result
        assert "ScriptType: v4.00+" in result

    def test_containsStyles(self):
        params = SubtitleParams(words=makeWords(("hi", 0.0, 0.5)))
        result = _buildAssFile(params)
        assert "[V4+ Styles]" in result
        assert "Default" in result

    def test_containsEvents(self):
        params = SubtitleParams(words=makeWords(("hi", 0.0, 0.5)))
        result = _buildAssFile(params)
        assert "[Events]" in result
        assert "Dialogue:" in result

    def test_emptyWordsNoDialogue(self):
        params = SubtitleParams(words=[])
        result = _buildAssFile(params)
        assert "Dialogue:" not in result

    def test_customFontAndSize(self):
        params = SubtitleParams(
            words=makeWords(("hi", 0.0, 0.5)),
            fontSize=72,
            fontName="Helvetica",
        )
        result = _buildAssFile(params)
        assert "Helvetica" in result
        assert "72" in result

    def test_positionBottom(self):
        params = SubtitleParams(
            words=makeWords(("hi", 0.0, 0.5)),
            position="bottom",
        )
        result = _buildAssFile(params)
        assert ",80," in result

    def test_positionTop(self):
        params = SubtitleParams(
            words=makeWords(("hi", 0.0, 0.5)),
            position="top",
        )
        result = _buildAssFile(params)
        assert ",80," in result


# ── integration tests (require ffmpeg + real media files) ─────────────────────

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.skipif(
    not (FIXTURES / "sample.mp4").exists(),
    reason="fixture files not present"
)
class TestAddSubtitles:
    def test_subtitlesProducesOutputFile(self):
        video = makeAsset(str(FIXTURES / "sample.mp4"), duration=5.0)
        params = SubtitleParams(words=makeWords(
            ("hello", 0.5, 1.0),
            ("world", 1.0, 1.5),
        ))

        result = addSubtitles(video, params)

        assert result.localPath is not None
        assert Path(result.localPath).exists()
        assert result.mimeType == "video/mp4"

    def test_subtitlesWithMultipleLines(self):
        video = makeAsset(str(FIXTURES / "sample.mp4"), duration=5.0)
        params = SubtitleParams(
            words=makeWords(
                ("one", 0.5, 0.8),
                ("two", 0.8, 1.1),
                ("three", 1.1, 1.4),
                ("four", 1.4, 1.7),
                ("five", 1.7, 2.0),
                ("six", 2.0, 2.3),
                ("seven", 2.3, 2.6),
            ),
            maxWordsPerLine=3,
        )

        result = addSubtitles(video, params)

        assert Path(result.localPath).exists()

    def test_subtitlesWithCustomStyle(self):
        video = makeAsset(str(FIXTURES / "sample.mp4"), duration=5.0)
        params = SubtitleParams(
            words=makeWords(("styled", 0.5, 1.0)),
            fontSize=72,
            fontName="Courier",
            position="top",
        )

        result = addSubtitles(video, params)

        assert Path(result.localPath).exists()

    def test_missingLocalPathAndB2KeyRaises(self):
        badAsset = Asset(id="x", source="upload", mimeType="video/mp4", duration=5.0)
        params = SubtitleParams(words=makeWords(("hi", 0.0, 0.5)))

        with pytest.raises(ValueError, match="neither localPath nor b2Key"):
            addSubtitles(badAsset, params)
