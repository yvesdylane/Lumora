from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://localhost:5432/lumora")
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret")
    b2_bucket: str = os.getenv("B2_BUCKET", "")
    b2_region: str = os.getenv("B2_REGION", "us-west-004")
    b2_key_id: str = os.getenv("B2_KEY_ID", "")
    b2_app_key: str = os.getenv("B2_APP_KEY", "")
    b2_public_url_base: str = os.getenv("B2_PUBLIC_URL_BASE", "")
    lumora_cache_dir: Path = Path(os.getenv("LUMORA_CACHE_DIR", str(Path(__file__).resolve().parent.parent / ".cache")))


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
