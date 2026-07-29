from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Manifest(BaseModel):
    runId: str | None = None
    data: dict[str, Any] = {}
