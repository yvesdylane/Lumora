from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from assets.controllers import assets as assetsController
from assets.schemas import (
    AssetListResponse,
    ImportResponse,
    ManifestResponse,
    PresignedUrlResponse,
    TagUpdateRequest,
)
from core.database import getSession

router = APIRouter(prefix="/api/assets", tags=["assets"])


def _assetToResponse(asset) -> ImportResponse:
    return ImportResponse(
        id=asset.id,
        source=asset.source,
        mimeType=asset.mimeType,
        duration=asset.duration,
        b2Key=asset.b2Key,
        localPath=asset.localPath,
        sha256=asset.sha256,
        manifestRef=asset.manifestRef,
        tags=asset.tags,
    )


@router.post("/import", response_model=ImportResponse, status_code=status.HTTP_201_CREATED)
async def importAsset(
    projectId: str = Form(...),
    kind: str = Form(...),
    file: UploadFile = File(...),
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        asset = await assetsController.importAsset(
            session,
            user=user,
            projectId=projectId,
            kind=kind,
            file=file,
        )
        return _assetToResponse(asset)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=AssetListResponse)
async def listAssets(
    projectId: str = Query(...),
    q: str | None = Query(None),
    tags: str | None = Query(None),
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    tagList = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    assets = await assetsController.searchAssets(
        session,
        user=user,
        projectId=projectId,
        query=q,
        tags=tagList,
    )
    return AssetListResponse(assets=[_assetToResponse(a) for a in assets])


@router.get("/{asset_id}", response_model=ImportResponse)
async def getAsset(
    asset_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    asset = await assetsController.getAsset(session, user=user, assetId=asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return _assetToResponse(asset)


@router.patch("/{asset_id}/tags", response_model=ImportResponse)
async def updateTags(
    asset_id: str,
    data: TagUpdateRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    asset = await assetsController.tagAsset(
        session,
        user=user,
        assetId=asset_id,
        tags=data.tags,
    )
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    return _assetToResponse(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteAsset(
    asset_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    deleted = await assetsController.deleteAsset(session, user=user, assetId=asset_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")


@router.get("/{asset_id}/manifest", response_model=ManifestResponse)
async def getManifest(
    asset_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        manifest = await assetsController.getManifest(session, user=user, assetId=asset_id)
        return ManifestResponse(runId=manifest.runId, data=manifest.data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{asset_id}/url", response_model=PresignedUrlResponse)
async def getAssetUrl(
    asset_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    asset = await assetsController.getAsset(session, user=user, assetId=asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    try:
        url = await assetsController.getPresignedUrl(asset=asset)
        return PresignedUrlResponse(url=url)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
