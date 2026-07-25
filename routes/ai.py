from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from controllers import ai as aiController
from core.ai.llmClient import GMIClient, LLMClient

router = APIRouter(prefix="/api/ai", tags=["ai-tier0"])


def getLLMClient() -> LLMClient:
    return GMIClient()


class CaptionsRequest(BaseModel):
    transcript: str
    wordTimings: list[dict]


class TransitionSuggestRequest(BaseModel):
    clipAMeta: dict
    clipBMeta: dict


class CutsSuggestRequest(BaseModel):
    timeline: dict
    targetDuration: float


class MotionSpecRequest(BaseModel):
    style: str
    layerType: str


@router.post("/captions/")
async def captions(
    data: CaptionsRequest,
    user: UserRow = Depends(getCurrentUser),
    client: LLMClient = Depends(getLLMClient),
):
    try:
        return await aiController.generateCaptions(client, data.transcript, data.wordTimings)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/transitions/suggest/")
async def transitionsSuggest(
    data: TransitionSuggestRequest,
    user: UserRow = Depends(getCurrentUser),
    client: LLMClient = Depends(getLLMClient),
):
    try:
        return await aiController.suggestTransition(client, data.clipAMeta, data.clipBMeta)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/cuts/suggest/")
async def cutsSuggest(
    data: CutsSuggestRequest,
    user: UserRow = Depends(getCurrentUser),
    client: LLMClient = Depends(getLLMClient),
):
    try:
        return await aiController.suggestCutPoints(client, data.timeline, data.targetDuration)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/motion-spec/")
async def motionSpec(
    data: MotionSpecRequest,
    user: UserRow = Depends(getCurrentUser),
    client: LLMClient = Depends(getLLMClient),
):
    try:
        return await aiController.generateMotionSpec(client, data.style, data.layerType)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
