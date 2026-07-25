from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
from typing import Any

from genblaze_core import ObjectLockConfig

from models.asset import Asset
from models.manifest import Manifest

from core.storage.backend import get_backend, getGenblazeSink
from core.storage.keys import manifestKey


def writeManifest(runId: str, manifest: dict[str, Any]) -> str:
    key = manifestKey(runId)
    payload = json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode("utf-8")
    backend = get_backend()
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
        backend.put(key, payload, content_type="application/json")
    return key


def getManifest(asset: Asset) -> Manifest:
    if not asset.manifestRef:
        raise ValueError("Asset.manifestRef is required to get a manifest")

    raw = get_backend().get(asset.manifestRef)
    data = json.loads(raw.decode("utf-8"))
    runId = data.get("run_id")
    if runId is None:
        runId = PurePosixPath(asset.manifestRef).stem
    return Manifest(run_id=runId, data=data)


def readGenblazeManifest(run: Any, *, verify: bool = True) -> Manifest:
    sink = getGenblazeSink()
    try:
        gbManifest = sink.read_manifest(run, verify=verify)
    finally:
        sink.close()

    if hasattr(gbManifest, "model_dump"):
        data = gbManifest.model_dump()
    elif hasattr(gbManifest, "to_dict"):
        data = gbManifest.to_dict()
    elif isinstance(gbManifest, dict):
        data = gbManifest
    else:
        data = dict(gbManifest)

    runId = getattr(run, "id", None) or data.get("run_id")
    return Manifest(run_id=runId, data=data)
