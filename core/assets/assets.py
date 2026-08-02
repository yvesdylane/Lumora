from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.assets.models import AssetRow
from models.asset import Asset, MediaInfo


async def importAsset(
    session: AsyncSession,
    *,
    userId: uuid.UUID,
    projectId: uuid.UUID,
    localPath: str,
    kind: str,
) -> Asset:
    path = Path(localPath)
    if not path.exists():
        raise FileNotFoundError(f"Asset not found: {localPath}")

    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    mimeType = _guessMime(path, kind)

    row = AssetRow(
        id=uuid.uuid4(),
        user_id=userId,
        project_id=projectId,
        source="upload",
        mime_type=mimeType,
        local_path=str(path.resolve()),
        sha256=sha256,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    return _rowToAsset(row)


async def getAsset(session: AsyncSession, assetId: uuid.UUID) -> Asset | None:
    result = await session.execute(select(AssetRow).where(AssetRow.id == assetId))
    row = result.scalar_one_or_none()
    return _rowToAsset(row) if row else None


async def persistStorageMetadata(
    session: AsyncSession,
    *,
    assetId: uuid.UUID,
    b2Key: str,
    sha256: str,
    duration: float | None = None,
) -> Asset | None:
    """Persist B2 object key + media info back onto an already-committed AssetRow."""
    row = await session.get(AssetRow, assetId)
    if row is None:
        return None
    row.b2_key = b2Key
    row.sha256 = sha256
    if duration is not None:
        row.duration = duration
    await session.commit()
    await session.refresh(row)
    return _rowToAsset(row)


async def persistGeneratedAsset(
    session: AsyncSession,
    *,
    userId: uuid.UUID,
    projectId: uuid.UUID,
    asset: Asset,
    source: Literal["upload", "ai"] = "ai",
) -> Asset:
    row = AssetRow(
        user_id=userId,
        project_id=projectId,
        source=source,
        mime_type=asset.mimeType,
        duration=asset.duration,
        b2_key=asset.b2Key,
        local_path=asset.localPath,
        sha256=asset.sha256,
        manifest_ref=asset.manifestRef,
        tags=asset.tags,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _rowToAsset(row)


async def searchAssets(
    session: AsyncSession,
    *,
    userId: uuid.UUID,
    projectId: uuid.UUID,
    query: str | None = None,
    tags: list[str] | None = None,
) -> list[Asset]:
    stmt = select(AssetRow).where(
        AssetRow.user_id == userId,
        AssetRow.project_id == projectId,
    )

    if query:
        stmt = stmt.where(AssetRow.mime_type.ilike(f"%{query}%"))

    if tags:
        stmt = stmt.where(AssetRow.tags.overlap(tags))

    result = await session.execute(stmt.order_by(AssetRow.created_at.desc()))
    return [_rowToAsset(row) for row in result.scalars().all()]


async def tagAsset(
    session: AsyncSession,
    assetId: uuid.UUID,
    tags: list[str],
) -> Asset | None:
    result = await session.execute(select(AssetRow).where(AssetRow.id == assetId))
    row = result.scalar_one_or_none()
    if row is None:
        return None

    existing = set(row.tags or [])
    existing.update(tags)
    row.tags = sorted(existing)
    await session.commit()
    await session.refresh(row)
    return _rowToAsset(row)


async def deleteAsset(session: AsyncSession, assetId: uuid.UUID) -> bool:
    result = await session.execute(select(AssetRow).where(AssetRow.id == assetId))
    row = result.scalar_one_or_none()
    if row is None:
        return False

    await session.delete(row)
    await session.commit()
    return True


def getMediaInfo(asset: Asset) -> MediaInfo:
    if asset.localPath is None:
        return MediaInfo()

    path = Path(asset.localPath)
    if not path.exists():
        return MediaInfo()

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return MediaInfo()
    if result.returncode != 0:
        return MediaInfo()

    data = json.loads(result.stdout)
    videoStream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    hasAudio = any(s.get("codec_type") == "audio" for s in data.get("streams", []))

    duration = float(data.get("format", {}).get("duration", 0))
    fps = None
    resolution = None
    codec = None

    if videoStream:
        codec = videoStream.get("codec_name")
        w = videoStream.get("width")
        h = videoStream.get("height")
        if w and h:
            resolution = (w, h)
        rawFps = videoStream.get("r_frame_rate", "")
        if "/" in rawFps:
            num, den = rawFps.split("/")
            if float(den) != 0:
                fps = round(float(num) / float(den), 2)
        elif rawFps:
            fps = float(rawFps)

    return MediaInfo(
        duration=duration,
        fps=fps,
        resolution=resolution,
        codec=codec,
        hasAudio=hasAudio,
    )


def _rowToAsset(row: AssetRow) -> Asset:
    return Asset(
        id=str(row.id),
        source=row.source,
        mimeType=row.mime_type,
        duration=float(row.duration) if row.duration else None,
        b2Key=row.b2_key,
        localPath=row.local_path,
        sha256=row.sha256,
        manifestRef=row.manifest_ref,
        tags=row.tags or [],
    )


def _guessMime(path: Path, kind: str) -> str:
    mapping = {
        "video": "video/mp4",
        "audio": "audio/mpeg",
        "image": "image/png",
    }
    return mapping.get(kind, "application/octet-stream")
