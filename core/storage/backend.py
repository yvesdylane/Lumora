from __future__ import annotations

from datetime import datetime, timedelta, timezone

from genblaze_core import KeyStrategy, ObjectLockConfig, ObjectStorageSink
from genblaze_s3 import S3StorageBackend

from utils.settings import get_settings

_backend: S3StorageBackend | None = None


def _make_backend(*, auto_lifecycle: bool = False) -> S3StorageBackend:
    settings = get_settings()
    return S3StorageBackend.for_backblaze(
        settings.b2_bucket,
        region=settings.b2_region,
        key_id=settings.b2_key_id,
        app_key=settings.b2_app_key,
        public_url_base=settings.b2_public_url_base,
        auto_lifecycle=auto_lifecycle,
    )


def get_backend() -> S3StorageBackend:
    """Lazy singleton S3StorageBackend for Lumora app asset ops."""
    global _backend
    if _backend is None:
        _backend = _make_backend(auto_lifecycle=True)
    return _backend


def close_backend() -> None:
    """Release the singleton backend connection pool (call on app shutdown)."""
    global _backend
    if _backend is not None:
        _backend.close()
        _backend = None


def get_genblaze_sink(
    *,
    manifest_lock: ObjectLockConfig | None = None,
) -> ObjectStorageSink:
    """
    Fresh ObjectStorageSink for a Genblaze pipeline run (single-use).

    Owns a dedicated backend so ``sink.close()`` (called by Pipeline.run)
    does not tear down the app singleton from ``get_backend()``.
    """
    lock = manifest_lock or ObjectLockConfig(
        retain_until=datetime.now(timezone.utc) + timedelta(days=365),
        mode="GOVERNANCE",
    )
    return ObjectStorageSink(
        _make_backend(auto_lifecycle=False),
        prefix="genblaze",
        key_strategy=KeyStrategy.HIERARCHICAL,
        manifest_lock=lock,
    )
