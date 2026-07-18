# core/media/subtitles.py

import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from models.subtitle import SubtitleParams, WordTiming


def addSubtitles(
    videoAsset: Asset,
    subtitleParams: SubtitleParams,
) -> Asset:
    """
    Burn karaoke-style captions onto a video using word-level timings.

    subtitleParams contains a list of WordTiming objects (word, start, end).
    Words are grouped into lines and rendered with ASS karaoke \\kf tags,
    producing a progressive color-fill reveal as each word is spoken.

    Returns a new Asset with localPath set to the subtitled output.
    """
    videoPath = _resolveLocalPath(videoAsset)
    outputPath = Path(tempfile.mkdtemp()) / f"{uuid.uuid4()}.mp4"

    assContent = _buildAssFile(subtitleParams)
    assPath = Path(tempfile.mkdtemp()) / f"{uuid.uuid4()}.ass"
    assPath.write_text(assContent)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(videoPath),
        "-vf", f"ass={assPath}",
        "-c:v", "libx264",
        "-c:a", "copy",
        str(outputPath),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg addSubtitles failed:\n{result.stderr}")

    return Asset(
        id=str(uuid.uuid4()),
        source=videoAsset.source,
        mimeType="video/mp4",
        duration=videoAsset.duration,
        b2Key=None,
        localPath=str(outputPath),
        sha256=None,
        manifestRef=None,
    )


def _buildAssFile(params: SubtitleParams) -> str:
    """Generate ASS subtitle content with karaoke \\kf tags from word timings."""
    lines = _groupWordsIntoLines(params.words, params.maxWordsPerLine)
    yPos = _getPositionY(params.position)

    header = _assHeader(params, yPos)
    events = _assEvents(lines)

    return f"{header}\n{events}\n"


def _groupWordsIntoLines(
    words: list[WordTiming], maxWordsPerLine: int
) -> list[list[WordTiming]]:
    """Group word timings into display lines, breaking on maxWordsPerLine."""
    if not words:
        return []

    grouped: list[list[WordTiming]] = []
    current: list[WordTiming] = []

    for word in words:
        current.append(word)
        if len(current) >= maxWordsPerLine:
            grouped.append(current)
            current = []

    if current:
        grouped.append(current)

    return grouped


def _assHeader(params: SubtitleParams, yPos: int) -> str:
    """Return the Script Info + Styles sections of the ASS file."""
    outline = params.outlineWidth
    return f"""[Script Info]
Title: Lumora Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{params.fontName},{params.fontSize},{params.primaryColor},&H000000FF,{params.outlineColor},&H80000000,0,0,0,0,100,100,0,0,1,{outline},1,2,10,10,{yPos},1"""


def _getPositionY(position: str) -> int:
    """Convert position name to ASS MarginV value."""
    mapping = {
        "top": 80,
        "center": 500,
        "bottom": 80,
    }
    return mapping.get(position, 80)


def _assEvents(lines: list[list[WordTiming]]) -> str:
    """Return the Events section with karaoke dialogue lines."""
    section = "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"

    for line in lines:
        startTime = _secondsToAssTime(line[0].start)
        endTime = _secondsToAssTime(line[-1].end)
        text = _buildKaraokeText(line)
        section += f"\nDialogue: 0,{startTime},{endTime},Default,,0,0,0,,{text}"

    return section


def _buildKaraokeText(words: list[WordTiming]) -> str:
    """Build ASS dialogue text with \\kf karaoke tags for each word."""
    parts: list[str] = []

    for i, w in enumerate(words):
        durationCs = int((w.end - w.start) * 100)
        parts.append(f"{{\\kf{durationCs}}}{w.word}")

    return " ".join(parts)


def _secondsToAssTime(seconds: float) -> str:
    """Convert seconds to ASS timestamp format H:MM:SS.CC."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _resolveLocalPath(asset: Asset) -> Path:
    """Return a local file path for the asset, downloading from B2 if needed."""
    if asset.localPath:
        return Path(asset.localPath)
    if asset.b2Key:
        from core.storage.b2 import downloadAsset
        downloaded = downloadAsset(asset.b2Key)
        return Path(downloaded.localPath)
    raise ValueError(f"Asset {asset.id} has neither localPath nor b2Key")
