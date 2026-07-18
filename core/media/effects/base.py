from __future__ import annotations

import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from models.effect import EffectParams

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FFMPEG = r"C:\Users\enowb\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"


def applySingleFilter(
    asset: Asset,
    filterString: str,
    startTime: float = 0.0,
    duration: float | None = None,
) -> Asset:
    """Apply a single ffmpeg filter string to a video asset.

    Handles time-range enable, temp filter script, subprocess call, and returns
    a new Asset. Effects call this instead of duplicating the ffmpeg plumbing.

    Args:
        asset: Source video.
        filterString: Raw ffmpeg filter (e.g. "gblur=sigma=10").
        startTime: When the effect begins (seconds). 0 = start of clip.
        duration: How long the effect lasts. None = full clip.

    Returns:
        New Asset pointing to the output video.
    """
    if asset.localPath is None:
        raise ValueError("Asset must have a localPath to apply an effect")

    inputPath = Path(asset.localPath)
    if not inputPath.exists():
        raise FileNotFoundError(f"Source video not found: {inputPath}")

    outputDir = _PROJECT_ROOT / "tmp" / "media"
    outputDir.mkdir(parents=True, exist_ok=True)
    outputPath = outputDir / f"{uuid.uuid4().hex}.mp4"

    fullFilter = _wrapFilterWithEnable(filterString, startTime, duration)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(fullFilter)
        scriptPath = f.name

    try:
        cmd = [
            FFMPEG,
            "-y",
            "-i", str(inputPath),
            "-filter_complex_script", scriptPath,
            "-map", "[out]",
            "-c:a", "copy",
            str(outputPath),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")
    finally:
        Path(scriptPath).unlink(missing_ok=True)

    return Asset(
        id=str(uuid.uuid4()),
        source=asset.source,
        mimeType="video/mp4",
        duration=asset.duration,
        localPath=str(outputPath.resolve()),
    )


def _wrapFilterWithEnable(
    filterString: str,
    startTime: float,
    duration: float | None,
) -> str:
    """Wrap a filter string with :enable='between(...)' when a time range is given.

    Three cases:
    - Single filter (no , or ;): append :enable directly.
    - Comma-chained filters (fade=t=in:...,fade=t=out:...): add :enable to EACH
      filter so they all respect the time range. Without this, only the last
      filter gets enable and the others run unconditionally.
    - Semicolon-chained filters (sepia's split/blend): append :enable to the
      last filter in the last chain. The last filter controls the final output,
      so when disabled it passes through its first input unchanged.
    """
    if duration is not None and duration > 0:
        endTime = startTime + duration
        enableExpr = f"enable='between(t,{startTime},{endTime})'"

        if ";" in filterString:
            return f"[0:v]{filterString}:{enableExpr}[out]"

        if "," in filterString:
            filters = filterString.split(",")
            enabledFilters = [f"{f}:{enableExpr}" for f in filters]
            return f"[0:v]{','.join(enabledFilters)}[out]"

        return f"[0:v]{filterString}:{enableExpr}[out]"
    return f"[0:v]{filterString}[out]"
