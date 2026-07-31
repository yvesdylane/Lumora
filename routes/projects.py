from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth.middlewares.auth import getCurrentUser
from auth.models import UserRow
from controllers import projects as projectsController
from core.database import getSession
from models.project import Project
from models.timeline import Timeline

router = APIRouter(prefix="/api/projects", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str


class UpdateProjectRequest(BaseModel):
    name: str


class CreateProjectResponse(BaseModel):
    project: Project
    timeline: Timeline


@router.post("/", response_model=CreateProjectResponse, status_code=status.HTTP_201_CREATED)
async def create(
    data: CreateProjectRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        return await projectsController.createProject(session, str(user.id), data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=list[Project])
async def list(
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    return await projectsController.listProjects(session, str(user.id))


@router.get("/{project_id}", response_model=Project)
async def get(
    project_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        return await projectsController.getProject(session, project_id, str(user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{project_id}/timeline")
async def getTimeline(
    project_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        return await projectsController.getTimeline(session, project_id, str(user.id))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.patch("/{project_id}", response_model=Project)
async def update(
    project_id: str,
    data: UpdateProjectRequest,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        return await projectsController.updateProject(session, project_id, str(user.id), data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    project_id: str,
    user: UserRow = Depends(getCurrentUser),
    session: AsyncSession = Depends(getSession),
):
    try:
        deleted = await projectsController.deleteProject(session, project_id, str(user.id))
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
