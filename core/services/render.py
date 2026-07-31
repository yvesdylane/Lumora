from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from core.renderer.renderer import renderTimeline
from core.services.composition import buildAssetRegistry, getProjectComposition
from models.asset import Asset


async def renderProject(
    session: AsyncSession,
    projectId: str,
) -> Asset:
    composition = await getProjectComposition(session, projectId)
    assetRegistry = await buildAssetRegistry(session, projectId)

    return await renderTimeline(composition, assetRegistry)
