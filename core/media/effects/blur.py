from __future__ import annotations

import hashlib
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from core.assets.assets import getMediaInfo

EFFECT_DIR = Path(tempfile.mkdtemp(prefix="lumora_effects_"))


def run(asset: Asset, params: dict) -> Asset:
    strength = params.get("strength", 5)
    src = Path(asset.localPath)
    out = EFFECT_DIR / f"blur_{uuid.uuid4().hex}.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf", f"boxblur={strength}:{strength}",
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "medium",
            "-c:a", "copy",
            str(out),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    result = Asset(
        id=str(uuid.uuid4()),
        source=asset.source,
        mimeType=asset.mimeType,
        localPath=str(out),
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        tags=list(asset.tags),
    )
    result.duration = getMediaInfo(result).duration
    return result
