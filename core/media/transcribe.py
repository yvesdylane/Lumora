# core/media/transcribe.py

import subprocess
import tempfile
from pathlib import Path

from faster_whisper import WhisperModel
from models.asset import Asset
from models.subtitle import WordTiming


_model: WhisperModel | None = None


def _getModel() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribeAudio(asset: Asset) -> list[WordTiming]:
    """
    Extract word-level timings from an asset's audio track using Whisper.

    Returns a list of WordTiming objects with word, start, and end times.
    """
    mediaPath = _resolveLocalPath(asset)
    audioPath = _extractAudio(mediaPath)

    model = _getModel()
    segments, _ = model.transcribe(
        str(audioPath),
        word_timestamps=True,
        language=None,
    )

    words: list[WordTiming] = []
    for segment in segments:
        if segment.words:
            for w in segment.words:
                words.append(WordTiming(
                    word=w.word.strip(),
                    start=round(w.start, 3),
                    end=round(w.end, 3),
                ))

    return words


def _extractAudio(mediaPath: Path) -> Path:
    """Extract audio track from a media file as mono 16kHz WAV for Whisper."""
    outputPath = Path(tempfile.mkdtemp()) / "audio.wav"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(mediaPath),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(outputPath),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg _extractAudio failed:\n{result.stderr}")

    return outputPath


def _resolveLocalPath(asset: Asset) -> Path:
    """Return a local file path for the asset, downloading from B2 if needed."""
    if asset.localPath:
        return Path(asset.localPath)
    if asset.b2Key:
        from core.storage.b2 import downloadAsset
        downloaded = downloadAsset(asset.b2Key)
        return Path(downloaded.localPath)
    raise ValueError(f"Asset {asset.id} has neither localPath nor b2Key")
