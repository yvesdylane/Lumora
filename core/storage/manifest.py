from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Any

from genblaze_core import ObjectLockConfig

from models.asset import Asset
from models.manifest import Manifest

from core.storage.backend import getBackend, getGenblazeSink
from core.storage.keys import manifestKey


def writeManifest(runId: str, manifest: dict[str, Any]) -> str:
    """
    Write a Lumora provenance manifest to manifests/{runId}.json.

    Applies Object Lock GOVERNANCE retention when the bucket supports it;
    falls back to an unlocked put otherwise. Returns the B2 key.
    """
    key = manifestKey(runId)
    payload = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf-8")
    backend = getBackend()
    lock = ObjectLockConfig(
        retain_until=datetime.now(timezone.utc) + timedelta(days=365),
        mode="GOVERNANCE",
    )
    try:
        backend.put(
            key,
            payload,
            content_type="application/json",
            object_lock=lock,
        )
    except Exception:
        # Bucket may not have Object Lock enabled at creation time.
        backend.put(key, payload, content_type="application/json")
    return key


def getManifest(asset: Asset) -> Manifest:
    """Fetch and parse the Lumora manifest referenced by asset.manifestRef."""
    if not asset.manifestRef:
        raise ValueError("Asset.manifestRef is required to get a manifest")

    raw = getBackend().get(asset.manifestRef)
    data = json.loads(raw.decode("utf-8"))
    runId = data.get("runId")
    if runId is None:
        runId = PurePosixPath(asset.manifestRef).stem
    return Manifest(runId=runId, data=data)


def readGenblazeManifest(run: Any, *, verify: bool = True) -> Manifest:
    """
    Read a Genblaze pipeline manifest via ObjectStorageSink (hash-verified).

    `run` must be a genblaze_core Run (or compatible object accepted by
    ObjectStorageSink.read_manifest).
    """
    sink = getGenblazeSink()
    try:
        gb_manifest = sink.read_manifest(run, verify=verify)
    finally:
        sink.close()

    if hasattr(gb_manifest, "model_dump"):
        data = gb_manifest.model_dump()
    elif hasattr(gb_manifest, "to_dict"):
        data = gb_manifest.to_dict()
    elif isinstance(gb_manifest, dict):
        data = gb_manifest
    else:
        data = dict(gb_manifest)  # type: ignore[arg-type]

    runId = getattr(run, "id", None) or data.get("runId")
    return Manifest(runId=runId, data=data)
