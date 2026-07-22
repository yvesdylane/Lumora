from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset
from core.assets.assets import getMediaInfo

TEST_DIR = Path(tempfile.mkdtemp(prefix="lumora_"))


def _probeStreams(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {}
    return json.loads(result.stdout)


def _streamsMatch(a: Asset, b: Asset) -> bool:
    if a.localPath is None or b.localPath is None:
        return False
    infoA = _probeStreams(Path(a.localPath))
    infoB = _probeStreams(Path(b.localPath))
    streamsA = {s["codec_name"]: s for s in infoA.get("streams", []) if s.get("codec_type") == "video"}
    streamsB = {s["codec_name"]: s for s in infoB.get("streams", []) if s.get("codec_type") == "video"}
    key = "h264"
    if key not in streamsA or key not in streamsB:
        return False
    sA, sB = streamsA[key], streamsB[key]
    return (
        sA.get("width") == sB.get("width")
        and sA.get("height") == sB.get("height")
        and sA.get("pix_fmt") == sB.get("pix_fmt")
    )


def separateAudioVideo(asset: Asset) -> tuple[Asset, Asset]:
    src = Path(asset.localPath)
    videoOut = TEST_DIR / f"video_{uuid.uuid4().hex}.mp4"
    audioOut = TEST_DIR / f"audio_{uuid.uuid4().hex}.mp3"

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-vn", "-c:a", "libmp3lame", str(audioOut)],
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-an", "-c:v", "copy", str(videoOut)],
        capture_output=True,
        check=True,
    )

    videoAsset = Asset(
        id=str(uuid.uuid4()),
        source=asset.source,
        mimeType="video/mp4",
        localPath=str(videoOut),
        sha256=hashlib.sha256(videoOut.read_bytes()).hexdigest(),
        tags=list(asset.tags),
    )
    audioAsset = Asset(
        id=str(uuid.uuid4()),
        source=asset.source,
        mimeType="audio/mpeg",
        localPath=str(audioOut),
        sha256=hashlib.sha256(audioOut.read_bytes()).hexdigest(),
        tags=list(asset.tags),
    )

    videoAsset.duration = getMediaInfo(videoAsset).duration
    audioAsset.duration = getMediaInfo(audioAsset).duration

    return videoAsset, audioAsset


def cutVideo(asset: Asset, start: float, end: float) -> Asset:
    src = Path(asset.localPath)
    out = TEST_DIR / f"cut_{uuid.uuid4().hex}.mp4"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-to", str(end),
            "-i", str(src),
            "-c", "copy",
            "-avoid_negative_ts", "make_zero",
            str(out),
        ],
        capture_output=True,
        check=True,
    )

    cutAsset = Asset(
        id=str(uuid.uuid4()),
        source=asset.source,
        mimeType=asset.mimeType,
        localPath=str(out),
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        tags=list(asset.tags),
    )
    cutAsset.duration = getMediaInfo(cutAsset).duration
    return cutAsset


def concatVideos(assets: list[Asset]) -> Asset:
    out = TEST_DIR / f"merged_{uuid.uuid4().hex}.mp4"
    allMatch = all(_streamsMatch(assets[0], a) for a in assets[1:])

    if allMatch and len(assets) > 1:
        listFile = TEST_DIR / f"concat_{uuid.uuid4().hex}.txt"
        listFile.write_text(
            "\n".join(f"file '{a.localPath}'" for a in assets)
        )
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(listFile),
                "-c", "copy",
                str(out),
            ],
            capture_output=True,
            check=True,
        )
    else:
        inputs = []
        filterParts = []
        for i, a in enumerate(assets):
            inputs.extend(["-i", a.localPath])
            filterParts.append(f"[{i}:v][{i}:a]")

        filterComplex = "".join(filterParts) + f"concat=n={len(assets)}:v=1:a=1[outv][outa]"

        subprocess.run(
            [
                "ffmpeg", "-y",
                *inputs,
                "-filter_complex", filterComplex,
                "-map", "[outv]",
                "-map", "[outa]",
                "-c:v", "libx264",
                "-crf", "23",
                "-preset", "medium",
                "-c:a", "aac",
                str(out),
            ],
            capture_output=True,
            check=True,
        )

    merged = Asset(
        id=str(uuid.uuid4()),
        source=assets[0].source if assets else "upload",
        mimeType=assets[0].mimeType if assets else "video/mp4",
        localPath=str(out),
        sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
        tags=list(assets[0].tags) if assets else [],
    )
    merged.duration = getMediaInfo(merged).duration
    return merged
