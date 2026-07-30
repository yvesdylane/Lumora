from __future__ import annotations

import logging
from datetime import datetime, timezone

from core.exports.exports import getExport, updateExportStatus
from core.exports.models import ExportRow
from core.jobs.notifications import broadcast
from core.renderer.assetResolver import buildAssetRegistry
from core.renderer.renderer import renderTimeline
from core.storage.b2 import upload_asset
from core.storage.cache import ensure_local
from core.storage.manifest import write_manifest
from core.timeline.composition import buildTimelineComposition
from core.database import asyncSession
from models.asset import Asset
from models.storage import StoragePrefix

logger = logging.getLogger(__name__)


async def dispatchRender(
    exportId: str,
    projectId: str,
    timelineId: str,
    outputFormat: str = "mp4",
) -> None:
    async with asyncSession() as session:
        try:
            export = await getExport(session, exportId)
            if export is None:
                logger.error(f"Export not found: {exportId}")
                return

            await updateExportStatus(session, exportId, "rendering")
            await broadcast(exportId, {"status": "rendering", "exportId": exportId})

            composition = await buildTimelineComposition(session, timelineId)

            assetIds = _collectAssetIds(composition)
            assets = await _resolveAssets(session, assetIds)
            assetRegistry = buildAssetRegistry(assets)

            rendered = await renderTimeline(composition, assetRegistry, outputFormat)

            uploaded = upload_asset(
                rendered,
                project_id=projectId,
                prefix=StoragePrefix.RENDERS,
                export_id=exportId,
            )

            manifest = {
                "run_id": exportId,
                "project_id": projectId,
                "timeline_id": timelineId,
                "type": "render",
                "output_format": outputFormat,
                "b2_key": uploaded.b2Key,
                "rendered_at": datetime.now(timezone.utc).isoformat(),
                "source_assets": list(assetRegistry.keys()),
            }
            write_manifest(exportId, manifest)

            await updateExportStatus(session, exportId, "completed", b2Key=uploaded.b2Key)
            await broadcast(exportId, {
                "status": "completed",
                "exportId": exportId,
                "b2Key": uploaded.b2Key,
            })

        except Exception as e:
            logger.error(f"Render failed for export {exportId}: {e}")
            await updateExportStatus(session, exportId, "failed", error=str(e))
            await broadcast(exportId, {
                "status": "failed",
                "exportId": exportId,
                "error": str(e),
            })


def _collectAssetIds(composition) -> list[str]:
    ids: set[str] = set()
    for track in composition.tracks:
        for layer in track.layers:
            if layer.layerType in ("clip", "audio", "text"):
                assetId = layer.params.get("assetId")
                if assetId:
                    ids.add(assetId)
    return list(ids)


async def _resolveAssets(
    session,
    assetIds: list[str],
) -> list[Asset]:
    from core.assets.models import AssetRow

    assets: list[Asset] = []
    for aid in assetIds:
        row = await session.get(AssetRow, aid)
        if row is None:
            logger.warning(f"Asset not found in DB: {aid}")
            continue
        asset = Asset(
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
        try:
            asset = ensure_local(asset)
        except Exception as e:
            logger.warning(f"Could not resolve asset {aid}: {e}")
            continue
        assets.append(asset)
    return assets
