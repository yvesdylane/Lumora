from __future__ import annotations

import uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from auth.models import UserRow
from core.assets import assets as assetsCore
from core.storage import b2 as b2Storage
from models.asset import Asset
from models.storage import StoragePrefix
from sqlalchemy.ext.asyncio import AsyncSession


async def importAsset(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    kind: str,
    file: UploadFile,
) -> Asset:
    projectIdUuid = uuid.UUID(projectId)

    suffix = Path(file.filename or "upload").suffix or ""
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmpPath = tmp.name

    asset = await assetsCore.importAsset(
        session,
        userId=user.id,
        projectId=projectIdUuid,
        localPath=tmpPath,
        kind=kind,
    )

    asset = b2Storage.upload_asset(
        asset,
        project_id=projectId,
        prefix=StoragePrefix.UPLOADS,
    )

    return asset


async def getAsset(
    session: AsyncSession,
    *,
    user: UserRow,
    assetId: str,
) -> Asset | None:
    return await assetsCore.getAsset(session, uuid.UUID(assetId))


async def searchAssets(
    session: AsyncSession,
    *,
    user: UserRow,
    projectId: str,
    query: str | None = None,
    tags: list[str] | None = None,
) -> list[Asset]:
    return await assetsCore.searchAssets(
        session,
        userId=user.id,
        projectId=uuid.UUID(projectId),
        query=query,
        tags=tags,
    )


async def tagAsset(
    session: AsyncSession,
    *,
    user: UserRow,
    assetId: str,
    tags: list[str],
) -> Asset | None:
    return await assetsCore.tagAsset(session, uuid.UUID(assetId), tags)


async def deleteAsset(
    session: AsyncSession,
    *,
    user: UserRow,
    assetId: str,
) -> bool:
    asset = await assetsCore.getAsset(session, uuid.UUID(assetId))
    if asset and asset.b2Key:
        from core.storage.backend import get_backend
        get_backend().delete(asset.b2Key)

    return await assetsCore.deleteAsset(session, uuid.UUID(assetId))


async def getPresignedUrl(
    *,
    asset: Asset,
) -> str:
    if not asset.b2Key:
        raise ValueError("Asset has no B2 key")
    return b2Storage.get_presigned_url(asset.b2Key)
