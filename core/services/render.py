from __future__ import annotations

from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from core.renderer.renderer import renderTimeline
from core.services.composition import buildAssetRegistry, getProjectComposition
from models.asset import Asset


async def renderProject(
    session: AsyncSession,
    projectId: str,
    outputFormat: Literal["mp4", "webm"] = "mp4",
) -> Asset:
    composition = await getProjectComposition(session, projectId)
    assetRegistry = await buildAssetRegistry(session, projectId)

    return await renderTimeline(composition, assetRegistry, outputFormat)
