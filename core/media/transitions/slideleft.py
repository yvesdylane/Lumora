from __future__ import annotations

from models.asset import Asset
from core.media.transitions._common import runXfade


def run(assetA: Asset, assetB: Asset, duration: float, easing: str) -> Asset:
    return runXfade(assetA, assetB, "slideleft", duration, easing)
