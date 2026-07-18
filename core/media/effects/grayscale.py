from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Convert video to grayscale.

    No params required — saturation set to 0.
    """
    filterStr = "hue=s=0"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
