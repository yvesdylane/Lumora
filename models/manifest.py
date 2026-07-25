from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class Manifest(BaseModel):
    run_id: str
    data: dict[str, Any] = {}
