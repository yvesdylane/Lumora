from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from assets.controllers import assets as assetsController
from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from core.database import getSession
from core.media.transcribe import transcribeAudio
from core.storage.cache import ensureLocal

router = APIRouter(prefix="/api", tags=["transcribe"])


class TranscribeRequest(BaseModel):
    assetId: str


class WordTimingResponse(BaseModel):
    word: str
    start: float = Field(..., ge=0)
    end: float = Field(..., ge=0)


class TranscribeResponse(BaseModel):
    assetId: str
    words: list[WordTimingResponse]


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    data: TranscribeRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    asset = await assetsController.getAsset(
        session,
        user=user,
        assetId=data.assetId,
    )
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    try:
        local = ensureLocal(asset)
        words = transcribeAudio(local)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return TranscribeResponse(
        assetId=data.assetId,
        words=[
            WordTimingResponse(word=w.word, start=w.start, end=w.end)
            for w in words
        ],
    )
