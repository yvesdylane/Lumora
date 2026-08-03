from __future__ import annotations

import math
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset, MediaInfo
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
from core.renderer.fonts import resolveFontFile

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

    fontColor = params.color
    boxColor = params.boxColor
    if params.opacity < 1.0:
        fontColor = f"{fontColor}@{params.opacity}"
        boxColor = f"{boxColor}@{params.opacity}"

    parts = [
        f"drawtext=text={escapeText}",
        f"fontfile={resolveFontFile(params)}",
        f"fontsize={params.size}",
        f"fontcolor={fontColor}",
        f"x={xExpr}",
        f"y={yExpr}",
    ]

    if params.outlineWidth > 0:
        parts.append(f"bordercolor={params.outlineColor}:borderw={params.outlineWidth}")

    if params.shadowX != 0 or params.shadowY != 0:
        shadowX = int(params.shadowX) if params.shadowX == int(params.shadowX) else params.shadowX
        shadowY = int(params.shadowY) if params.shadowY == int(params.shadowY) else params.shadowY
        parts.append(
            f"shadowcolor={params.shadowColor}:shadowx={shadowX}:shadowy={shadowY}"
        )

    if params.box:
        parts.append(f"box=1:boxcolor={boxColor}:boxborderw={params.boxBorderW}")
    elif params.bgColor:
        bgOpacity = params.opacity if params.opacity < 1.0 else 0.6
        parts.append(f"box=1:boxcolor={params.bgColor}@{bgOpacity}:boxborderw=8")

    start = params.startTime
    end = start + (params.duration or videoDuration - start)
    parts.append(f"enable=between(t\\,{start}\\,{end})")

    return ":".join(parts)


def buildFilterComplexGraph(
    textLayers: list[TextParams],
    effectLayers: list[EffectParams],
    width: int,
    height: int,
    duration: float,
    fps: float,
) -> tuple[list[str], str]:
    """Build (extra ffmpeg inputs, filter_complex string) for text/effect overlays.

    Each text layer is drawn onto its own transparent full-frame source, rotated
    about its center when rotation != 0, then overlaid at width*(x-0.5),
    height*(y-0.5). The drawtext filter already center-anchors text at (w*x, h*y),
    so the overlay offset preserves the anchor through rotation.
    """
    inputs: list[str] = []
    graph: list[str] = []

    effectChain = ",".join(buildEffectFilter(e) for e in effectLayers)
    graph.append(f"[0:v]{effectChain if effectChain else 'null'}[base]")

    cur = "[base]"
    for i, t in enumerate(textLayers):
        idx = i + 1
        inputs.extend(
            [
                "-f", "lavfi",
                "-i", f"color=black@0:s={width}x{height}:d={duration}:r={int(fps)}",
            ]
        )
        layer = buildTextFilter(t, duration)
        if t.rotation != 0:
            layer = (
                f"{layer},rotate={math.radians(t.rotation)}:fillcolor=0x00000000,format=rgba"
            )
        graph.append(f"[{idx}:v]{layer}[t{i}]")
        px = float(t.position.get("x", 0.5))
        py = float(t.position.get("y", 0.9))
        ox = width * (px - 0.5)
        oy = height * (py - 0.5)
        oxStr = int(ox) if ox == int(ox) else ox
        oyStr = int(oy) if oy == int(oy) else oy
        graph.append(f"{cur}[t{i}]overlay=x={oxStr}:y={oyStr}:format=auto[v{i}]")
        cur = f"[v{i}]"

    return inputs, ";".join(graph)


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

    if any(t.rotation != 0 for t in textLayers):
        return _applyVideoFiltersComplex(src, videoAsset, info, textLayers, effectLayers, out)

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

    return _newFilteredAsset(videoAsset, out)


def _applyVideoFiltersComplex(
    src: Path,
    videoAsset: Asset,
    info: MediaInfo,
    textLayers: list[TextParams],
    effectLayers: list[EffectParams],
    out: Path,
) -> Asset:
    width, height = info.resolution or (1920, 1080)
    duration = info.duration or 5.0
    fps = info.fps or 30

    inputs, filterComplex = buildFilterComplexGraph(
        textLayers,
        effectLayers,
        width,
        height,
        duration,
        fps,
    )

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(src),
            *inputs,
            "-filter_complex", filterComplex,
            "-map", "[v%d]" % (len(textLayers) - 1),
            "-map", "0:a?",
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

    return _newFilteredAsset(videoAsset, out)


def _newFilteredAsset(videoAsset: Asset, out: Path) -> Asset:
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
