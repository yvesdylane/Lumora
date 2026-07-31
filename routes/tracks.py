from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from controllers import tracks as tracksController
from core.database import getSession
from models.tracks import CreateTrackRequest, TrackResponse

router = APIRouter(prefix="/api/timelines/{timelineId}/tracks", tags=["tracks"])


@router.post("/", response_model=TrackResponse, status_code=status.HTTP_201_CREATED)
async def createTrack(
    timelineId: str,
    data: CreateTrackRequest,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    track = await tracksController.createTrack(
        session, timelineId, str(user.id), data.kind
    )
    return TrackResponse.model_validate(track)


@router.get("/", response_model=list[TrackResponse])
async def listTracks(
    timelineId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    tracks = await tracksController.listTracks(session, timelineId, str(user.id))
    return [TrackResponse.model_validate(t) for t in tracks]


@router.delete("/{trackId}", status_code=status.HTTP_204_NO_CONTENT)
async def deleteTrack(
    timelineId: str,
    trackId: str,
    session: AsyncSession = Depends(getSession),
    user: UserRow = Depends(getCurrentUser),
):
    await tracksController.deleteTrack(session, trackId, timelineId, str(user.id))
