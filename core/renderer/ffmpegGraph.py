from __future__ import annotations

import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from models.renderParams import (
    AudioParams,
    BlurParams,
    BrightnessParams,
    ContrastParams,
    EffectParams,
    GrayscaleParams,
    TextParams,
)
from core.assets.assets import getMediaInfo

RENDER_DIR = Path(tempfile.mkdtemp(prefix="lumora_render_"))


def buildTextFilter(params: TextParams, videoDuration: float) -> str:
    x = params.position.get("x", 0.5)
    y = params.position.get("y", 0.9)

    if isinstance(x, float) and x <= 1.0:
        xExpr = f"(w*{x})-(text_w/2)"
    else:
        xExpr = str(x)

    if isinstance(y, float) and y <= 1.0:
        yExpr = f"(h*{y})-(text_h/2)"
    else:
        yExpr = str(y)

    escapeText = params.text.replace(":", "\\:").replace("'", "\\'")

    parts = [
        f"drawtext=text={escapeText}",
        f"fontsize={params.size}",
        f"fontcolor={params.color}",
        f"x={xExpr}",
        f"y={yExpr}",
    ]

    if params.bgColor:
        parts.append(f"box=1:boxcolor={params.bgColor}@0.6:boxborderw=8")

    start = params.startTime
    end = start + (params.duration or videoDuration - start)
    parts.append(f"enable=between(t\\,{start}\\,{end})")

    return ":".join(parts)


def buildEffectFilter(params: EffectParams) -> str:
    if isinstance(params, BlurParams):
        return f"boxblur={params.strength}:{params.strength}"
    elif isinstance(params, BrightnessParams):
        return f"eq=brightness={params.factor - 1.0}"
    elif isinstance(params, ContrastParams):
        return f"eq=contrast={params.factor}"
    elif isinstance(params, GrayscaleParams):
        return "hue=s=0"
    else:
        raise ValueError(f"Unknown effect type: {params.filterType}")


def applyVideoFilters(
    videoAsset: Asset,
    textLayers: list[TextParams],
    effectLayers: list[EffectParams],
) -> Asset:
    if not textLayers and not effectLayers:
        return videoAsset

    info = getMediaInfo(videoAsset)
    src = Path(videoAsset.localPath)
    out = RENDER_DIR / f"filtered_{uuid.uuid4().hex}.mp4"

    filters = []
    for e in effectLayers:
        filters.append(buildEffectFilter(e))

    for t in textLayers:
        filters.append(buildTextFilter(t, info.duration or 0))

    if not filters:
        return videoAsset

    filterChain = ",".join(filters)

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            "-vf", filterChain,
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

    filtered = Asset(
        id=str(uuid.uuid4()),
        source=videoAsset.source,
        mimeType=videoAsset.mimeType,
        localPath=str(out),
        sha256=_sha256(out),
        tags=list(videoAsset.tags),
    )
    filtered.duration = getMediaInfo(filtered).duration
    return filtered


def mixAudioTracks(
    videoAsset: Asset,
    audioAssets: list[tuple[Asset, AudioParams]],
) -> Asset:
    if not audioAssets:
        return videoAsset

    src = Path(videoAsset.localPath)
    out = RENDER_DIR / f"audio_mixed_{uuid.uuid4().hex}.mp4"

    inputs = ["-i", str(src)]
    filterParts = []
    audioLabels = []

    for idx, (audioAsset, params) in enumerate(audioAssets):
        inputs.extend(["-i", str(audioAsset.localPath)])
        vol = params.volume
        fadeParts = [f"volume={vol}"]
        if params.fadeIn > 0:
            fadeParts.append(f"afade=t=in:st=0:d={params.fadeIn}")
        if params.fadeOut > 0:
            dur = getMediaInfo(audioAsset).duration or 0
            fadeParts.append(f"afade=t=out:st={dur - params.fadeOut}:d={params.fadeOut}")
        audioChain = ",".join(fadeParts)
        filterParts.append(f"[{idx + 1}:a]{audioChain}[a{idx}]")
        audioLabels.append(f"[a{idx}]")

    audioMixInputs = "".join(audioLabels)
    if len(audioLabels) > 1:
        filterParts.append(
            f"{audioMixInputs}amix=inputs={len(audioLabels)}:duration=first[outa]"
        )
        audioOutput = "[outa]"
    else:
        filterParts.append(f"{audioLabels[0]}acopy[outa]")
        audioOutput = "[outa]"

    filterComplex = ";".join(filterParts)

    subprocess.run(
        [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filterComplex,
            "-map", "0:v",
            "-map", audioOutput,
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
        sha256=_sha256(out),
        tags=list(videoAsset.tags),
    )
    mixed.duration = getMediaInfo(mixed).duration
    return mixed


def _sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()
