from __future__ import annotations

import hashlib
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from core.assets.assets import getMediaInfo

TEXT_DIR = Path(tempfile.mkdtemp(prefix="lumora_text_"))


def addTextOverlay(
    asset: Asset,
    text: str,
    font: str = "Arial",
    size: int = 48,
    color: str = "white",
    position: dict | None = None,
    startTime: float = 0.0,
    duration: float | None = None,
    bgColor: str | None = None,
) -> Asset:
    if position is None:
        position = {"x": 0.5, "y": 0.9}

    src = Path(asset.localPath)
    out = TEXT_DIR / f"text_{uuid.uuid4().hex}.mp4"

    info = getMediaInfo(asset)
    videoDuration = info.duration or 0

    x = position.get("x", 0.5)
    y = position.get("y", 0.9)

    if isinstance(x, float) and x <= 1.0:
        xExpr = f"(w*{x})-(text_w/2)"
    else:
        xExpr = str(x)

    if isinstance(y, float) and y <= 1.0:
        yExpr = f"(h*{y})-(text_h/2)"
    else:
        yExpr = str(y)

    escapeText = text.replace(":", "\\:").replace("'", "\\'")

    parts = [
        f"drawtext=text={escapeText}",
        f"fontsize={size}",
        f"fontcolor={color}",
        f"x={xExpr}",
        f"y={yExpr}",
    ]

    if bgColor:
        parts.append(f"box=1:boxcolor={bgColor}@0.6:boxborderw=8")

    end = startTime + (duration or videoDuration - startTime)
    parts.append(f"enable=between(t\\,{startTime}\\,{end})")

    filterStr = ":".join(parts)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf", filterStr,
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

    textAsset = Asset(
        id=str(uuid.uuid4()),
        source=asset.source,
        mimeType=asset.mimeType,
        localPath=str(out),
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        tags=list(asset.tags),
    )
    textAsset.duration = getMediaInfo(textAsset).duration
    return textAsset
