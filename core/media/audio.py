from __future__ import annotations

import hashlib
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from core.assets.assets import getMediaInfo

AUDIO_DIR = Path(tempfile.mkdtemp(prefix="lumora_audio_"))


def mixAudioLayer(
    videoAsset: Asset,
    audioAsset: Asset,
    volume: float = 1.0,
    fadeIn: float = 0.0,
    fadeOut: float = 0.0,
    startTime: float = 0.0,
) -> Asset:
    src = Path(videoAsset.localPath)
    audioSrc = Path(audioAsset.localPath)
    out = AUDIO_DIR / f"audio_mixed_{uuid.uuid4().hex}.mp4"

    audioDuration = getMediaInfo(audioAsset).duration or 0

    audioFilters = [f"volume={volume}"]

    if fadeIn > 0:
        audioFilters.append(f"afade=t=in:st=0:d={fadeIn}")
    if fadeOut > 0:
        fadeStart = audioDuration - fadeOut
        if fadeStart > 0:
            audioFilters.append(f"afade=t=out:st={fadeStart}:d={fadeOut}")
    if startTime > 0:
        delay_ms = int(startTime * 1000)
        audioFilters.append(f"adelay={delay_ms}|{delay_ms}")

    audioChain = ",".join(audioFilters)

    filterComplex = f"[1:a]{audioChain}[aext];[0:a][aext]amix=inputs=2:duration=first[outa]"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            "-i", str(audioSrc),
            "-filter_complex", filterComplex,
            "-map", "0:v",
            "-map", "[outa]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    mixed = Asset(
        id=str(uuid.uuid4()),
        source=videoAsset.source,
        mimeType=videoAsset.mimeType,
        localPath=str(out),
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        tags=list(videoAsset.tags),
    )
    mixed.duration = getMediaInfo(mixed).duration
    return mixed
