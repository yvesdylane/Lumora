from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    b2_key_id: str = os.getenv("keyID", "")
    b2_app_key: str = os.getenv("applicationKey", "")
    b2_bucket: str = os.getenv("bucketsName", "")
    b2_region: str = os.getenv("region", "us-east-005")
    b2_public_url_base: str = os.getenv("B2_PUBLIC_URL_BASE", "")

    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    lumora_cache_dir: Path = Path(
        os.getenv("LUMORA_CACHE_DIR", Path.home() / ".lumora" / "cache")
    )


@lru_cache
def getSettings() -> Settings:
    return Settings()
