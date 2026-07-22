from __future__ import annotations

from models.storage import StoragePrefix
from utils.mime import extension_for_mime


def build_key(
    prefix: StoragePrefix | str,
    *,
    project_id: str | None = None,
    run_id: str | None = None,
    asset_id: str | None = None,
    export_id: str | None = None,
    mime_type: str | None = None,
    filename: str | None = None,
) -> str:
    """Build a Lumora B2 object key under the canonical prefix layout."""
    root = str(prefix).rstrip("/")

    if root == StoragePrefix.MANIFESTS:
        if not run_id:
            raise ValueError("run_id is required for manifests/")
        return f"{root}/{run_id}.json"

    if root == StoragePrefix.STAGING:
        if not run_id or not asset_id:
            raise ValueError("run_id and asset_id are required for staging/")
        ext = extension_for_mime(mime_type) if mime_type else ""
        return f"{root}/{run_id}/{asset_id}{ext}"

    if root == StoragePrefix.RENDERS:
        if not project_id or not export_id:
            raise ValueError("project_id and export_id are required for renders/")
        return f"{root}/{project_id}/{export_id}.mp4"

    if root in (
        StoragePrefix.UPLOADS,
        StoragePrefix.GENERATED_AUDIO,
        StoragePrefix.GENERATED_IMAGE,
    ):
        if not project_id or not asset_id:
            raise ValueError(f"project_id and asset_id are required for {root}/")
        if filename:
            return f"{root}/{project_id}/{filename}"
        ext = extension_for_mime(mime_type) if mime_type else ""
        return f"{root}/{project_id}/{asset_id}{ext}"

    raise ValueError(f"Unknown storage prefix: {root}")


def staging_prefix(run_id: str) -> str:
    return f"{StoragePrefix.STAGING}/{run_id}/"


def manifest_key(run_id: str) -> str:
    return build_key(StoragePrefix.MANIFESTS, run_id=run_id)
