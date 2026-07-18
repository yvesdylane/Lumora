# core/media/image.py

import subprocess
import tempfile
import uuid
from pathlib import Path

from models.asset import Asset


def generateThumbnail(
    videoAsset: Asset,
    timestamp: float = 1.0,
) -> Asset:
    """
    Extract a single JPEG thumbnail frame from a video.

    timestamp: seconds into the video to grab the frame (default 1.0s).
    Returns a new Asset with localPath pointing to the JPEG file.
    """
    videoPath = _resolveLocalPath(videoAsset)
    outputPath = Path(tempfile.mkdtemp()) / f"{uuid.uuid4()}.jpg"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(videoPath),
        "-ss", str(timestamp),
        "-frames:v", "1",
        "-q:v", "2",
        str(outputPath),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg generateThumbnail failed:\n{result.stderr}")

    return Asset(
        id=str(uuid.uuid4()),
        source=videoAsset.source,
        mimeType="image/jpeg",
        localPath=str(outputPath),
    )


def extractFrame(
    videoAsset: Asset,
    timestamp: float,
    format: str = "png",
) -> Asset:
    """
    Extract a single frame from a video at any timestamp.

    format: 'png' (lossless) or 'jpg' (compressed).
    Returns a new Asset with localPath pointing to the extracted frame.
    """
    videoPath = _resolveLocalPath(videoAsset)
    ext = "png" if format == "png" else "jpg"
    outputPath = Path(tempfile.mkdtemp()) / f"{uuid.uuid4()}.{ext}"

    qualityArgs = []
    if ext == "jpg":
        qualityArgs = ["-q:v", "2"]

    cmd = [
        "ffmpeg", "-y",
        "-i", str(videoPath),
        "-ss", str(timestamp),
        "-frames:v", "1",
        *qualityArgs,
        str(outputPath),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg extractFrame failed:\n{result.stderr}")

    mimeType = "image/png" if ext == "png" else "image/jpeg"
    return Asset(
        id=str(uuid.uuid4()),
        source=videoAsset.source,
        mimeType=mimeType,
        localPath=str(outputPath),
    )


def addImageOverlay(
    videoAsset: Asset,
    imageAsset: Asset,
    position: dict,
    startTime: float,
    duration: float,
) -> Asset:
    """
    Overlay an image onto a video for a specified duration.

    position: {"x": int, "y": int} — top-left corner in pixels,
              or {"x": "center", "y": "center"} to auto-center.
    startTime: when the overlay appears (seconds).
    duration: how long the overlay stays visible (seconds).

    Returns a new Asset with the overlay burned in.
    """
    videoPath = _resolveLocalPath(videoAsset)
    imagePath = _resolveLocalPath(imageAsset)
    outputPath = Path(tempfile.mkdtemp()) / f"{uuid.uuid4()}.mp4"

    x, y = _resolvePosition(position, videoPath, imagePath)
    endTime = startTime + duration

    filterComplex = (
        f"[1:v]format=rgba[ovr];"
        f"[0:v][ovr]overlay={x}:{y}:"
        f"enable='between(t\\,{startTime}\\,{endTime})':"
        f"shortest=1"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(videoPath),
        "-i", str(imagePath),
        "-filter_complex", filterComplex,
        "-c:v", "libx264",
        "-c:a", "copy",
        str(outputPath),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg addImageOverlay failed:\n{result.stderr}")

    return Asset(
        id=str(uuid.uuid4()),
        source=videoAsset.source,
        mimeType="video/mp4",
        duration=videoAsset.duration,
        localPath=str(outputPath),
    )


def _resolvePosition(
    position: dict,
    videoPath: Path,
    imagePath: Path,
) -> tuple[str, str]:
    """Convert position dict to ffmpeg overlay x:y strings."""
    rawX = position.get("x", 0)
    rawY = position.get("y", 0)

    if rawX == "center" or rawY == "center":
        xExpr = f"(main_w-overlay_w)/2" if rawX == "center" else str(rawX)
        yExpr = f"(main_h-overlay_h)/2" if rawY == "center" else str(rawY)
        return xExpr, yExpr

    return str(rawX), str(rawY)


def _resolveLocalPath(asset: Asset) -> Path:
    """Return a local file path for the asset, downloading from B2 if needed."""
    if asset.localPath:
        return Path(asset.localPath)
    if asset.b2Key:
        from core.storage.b2 import downloadAsset
        downloaded = downloadAsset(asset.b2Key)
        return Path(downloaded.localPath)
    raise ValueError(f"Asset {asset.id} has neither localPath nor b2Key")
