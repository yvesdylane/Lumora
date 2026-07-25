from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from core.assets.assets import getMediaInfo

TRANSITION_DIR = Path(tempfile.mkdtemp(prefix="lumora_transitions_"))


def _probeFps(src: Path) -> float:
    """Get fps from a video file via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-print_format", "json",
            str(src),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return 30.0
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    if not streams:
        return 30.0
    raw = streams[0].get("r_frame_rate", "30/1")
    if "/" in raw:
        num, den = raw.split("/")
        if float(den) != 0:
            return round(float(num) / float(den), 2)
    return float(raw) if raw else 30.0


def runXfade(assetA: Asset, assetB: Asset, xfadeName: str, duration: float, easing: str) -> Asset:
    srcA = Path(assetA.localPath)
    srcB = Path(assetB.localPath)

    infoA = getMediaInfo(assetA)
    infoB = getMediaInfo(assetB)
    offset = (infoA.duration or 0.0) - duration
    if offset < 0:
        offset = 0

    wA, hA = infoA.resolution or (1920, 1080)
    wB, hB = infoB.resolution or (1920, 1080)

    fpsA = _probeFps(srcA)
    fpsB = _probeFps(srcB)
    targetFps = max(fpsA, fpsB)

    canvasW = max(wA, wB)
    canvasH = max(hA, hB)

    out = TRANSITION_DIR / f"transition_{uuid.uuid4().hex}.mp4"

    needsNorm = (wA != canvasW or hA != canvasH or wB != canvasW or hB != canvasH
                 or abs(fpsA - fpsB) > 0.5)

    if needsNorm:
        filterComplex = (
            f"[0:v]scale={canvasW}:{canvasH}:force_original_aspect_ratio=decrease,"
            f"pad={canvasW}:{canvasH}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={targetFps},setsar=1,format=yuv420p[v0];"
            f"[1:v]scale={canvasW}:{canvasH}:force_original_aspect_ratio=decrease,"
            f"pad={canvasW}:{canvasH}:(ow-iw)/2:(oh-ih)/2:black,"
            f"fps={targetFps},setsar=1,format=yuv420p[v1];"
            f"[v0][v1]xfade=transition={xfadeName}:duration={duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={duration}[a]"
        )
    else:
        filterComplex = (
            f"[0:v]format=yuv420p[v0];"
            f"[1:v]format=yuv420p[v1];"
            f"[v0][v1]xfade=transition={xfadeName}:duration={duration}:offset={offset}[v];"
            f"[0:a][1:a]acrossfade=d={duration}[a]"
        )

    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(srcA),
            "-i", str(srcB),
            "-filter_complex", filterComplex,
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libopenh264",
            "-c:a", "aac",
            str(out),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg xfade failed (code {result.returncode}):\n{result.stderr}"
        )

    merged = Asset(
        id=str(uuid.uuid4()),
        source=assetA.source,
        mimeType=assetA.mimeType,
        localPath=str(out),
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        tags=list(assetA.tags),
    )
    merged.duration = getMediaInfo(merged).duration
    return merged
