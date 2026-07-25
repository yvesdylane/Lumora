from __future__ import annotations

from datetime import datetime, timedelta, timezone

from genblaze_core import KeyStrategy, ObjectLockConfig, ObjectStorageSink
from genblaze_s3 import S3StorageBackend

from utils.settings import get_settings

_backend: S3StorageBackend | None = None


def _makeBackend(*, autoLifecycle: bool = False) -> S3StorageBackend:
    settings = get_settings()
    return S3StorageBackend.for_backblaze(
        settings.b2_bucket,
        region=settings.b2_region,
        key_id=settings.b2_key_id,
        app_key=settings.b2_app_key,
        public_url_base=settings.b2_public_url_base,
        auto_lifecycle=autoLifecycle,
    )


def get_backend() -> S3StorageBackend:
    global _backend
    if _backend is None:
        _backend = _makeBackend(autoLifecycle=True)
    return _backend


def close_backend() -> None:
    global _backend
    if _backend is not None:
        _backend.close()
        _backend = None


def getGenblazeSink(
    *,
    manifestLock: ObjectLockConfig | None = None,
) -> ObjectStorageSink:
    lock = manifestLock or ObjectLockConfig(
        retain_until=datetime.now(timezone.utc) + timedelta(days=365),
        mode="GOVERNANCE",
    )
    return ObjectStorageSink(
        _makeBackend(autoLifecycle=False),
        prefix="genblaze",
        key_strategy=KeyStrategy.HIERARCHICAL,
        manifest_lock=lock,
    )
