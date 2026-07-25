from __future__ import annotations

from models.storage import StoragePrefix
from utils.mime import extension_for_mime


def build_key(
    prefix: StoragePrefix | str,
    *,
    projectId: str | None = None,
    runId: str | None = None,
    assetId: str | None = None,
    exportId: str | None = None,
    mimeType: str | None = None,
    filename: str | None = None,
) -> str:
    root = prefix.value.rstrip("/") if hasattr(prefix, "value") else str(prefix).rstrip("/")

    if root == StoragePrefix.MANIFESTS:
        if not runId:
            raise ValueError("runId is required for manifests/")
        return f"{root}/{runId}.json"

    if root == StoragePrefix.STAGING:
        if not runId or not assetId:
            raise ValueError("runId and assetId are required for staging/")
        ext = extension_for_mime(mimeType) if mimeType else ""
        return f"{root}/{runId}/{assetId}{ext}"

    if root == StoragePrefix.RENDERS:
        if not projectId or not exportId:
            raise ValueError("projectId and exportId are required for renders/")
        return f"{root}/{projectId}/{exportId}.mp4"

    if root in (
        StoragePrefix.UPLOADS,
        StoragePrefix.GENERATED_AUDIO,
        StoragePrefix.GENERATED_IMAGE,
    ):
        if not projectId or not assetId:
            raise ValueError(f"projectId and assetId are required for {root}/")
        if filename:
            return f"{root}/{projectId}/{filename}"
        ext = extension_for_mime(mimeType) if mimeType else ""
        return f"{root}/{projectId}/{assetId}{ext}"

    raise ValueError(f"Unknown storage prefix: {root}")


def stagingPrefix(runId: str) -> str:
    return f"{StoragePrefix.STAGING.value}/{runId}/"


def manifestKey(runId: str) -> str:
    return build_key(StoragePrefix.MANIFESTS, runId=runId)
