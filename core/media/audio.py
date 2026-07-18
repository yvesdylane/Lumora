# core/media/audio.py

import subprocess
import tempfile
import uuid
from pathlib import Path
from models.asset import Asset


def mixAudioLayer(
    videoAsset: Asset,
    audioAsset: Asset,
    volumeEnvelope: list[dict],
    startTime: float,
) -> Asset:
    """
    Mix an audio asset into a video asset starting at startTime.

    volumeEnvelope: list of {"time": float, "volume": float} keyframes.
    Volume values are 0.0 (silent) to 1.0 (full). Linear interpolation
    between keyframes is applied via ffmpeg's volume filter.

    Returns a new Asset with a local_path set to the mixed output.
    The caller is responsible for uploading to B2 if needed.
    """
    videoPath = _resolveLocalPath(videoAsset)
    audioPath = _resolveLocalPath(audioAsset)

    outputPath = Path(tempfile.mkdtemp()) / f"{uuid.uuid4()}.mp4"

    volumeFilter = _buildVolumeFilter(volumeEnvelope)
    delayMs = int(startTime * 1000)

    # adelay shifts audio start; volume filter applies the envelope
    audioFilterChain = f"adelay={delayMs}|{delayMs},{volumeFilter}"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(videoPath),
        "-i", str(audioPath),
        "-filter_complex",
        f"[1:a]{audioFilterChain}[aout];[0:a][aout]amix=inputs=2:duration=first[mix]",
        "-map", "0:v",
        "-map", "[mix]",
        "-c:v", "copy",
        "-c:a", "aac",
        str(outputPath),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg mixAudioLayer failed:\n{result.stderr}")

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


def _buildVolumeFilter(envelope: list[dict]) -> str:
    """Convert volume envelope keyframes to an ffmpeg volume filter string."""
    if not envelope:
        return "volume=1.0"

    # Single keyframe = static volume
    if len(envelope) == 1:
        return f"volume={envelope[0]['volume']}"

    # Multiple keyframes = dynamic volume using ffmpeg eval=frame
    points = "|".join(
        f"{kf['time']}:{kf['volume']}" for kf in sorted(envelope, key=lambda k: k["time"])
    )
    return f"volume='if(lt(t,{envelope[0]['time']}),{envelope[0]['volume']},lerp({envelope[0]['volume']},{envelope[-1]['volume']},(t-{envelope[0]['time']})/({envelope[-1]['time']}-{envelope[0]['time']})))':eval=frame"


def _resolveLocalPath(asset: Asset) -> Path:
    """Return a local file path for the asset, downloading from B2 if needed."""
    if asset.localPath:
        return Path(asset.localPath)
    if asset.b2Key:
        from core.storage.b2 import downloadAsset
        downloaded = downloadAsset(asset.b2Key)
        return Path(downloaded.localPath)
    raise ValueError(f"Asset {asset.id} has neither localPath nor b2Key")