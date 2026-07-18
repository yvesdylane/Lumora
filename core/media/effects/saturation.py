from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Adjust video color saturation.

    params.params:
        value (float): Saturation multiplier. 0.0 = grayscale, 1.0 = normal, 3.0 = vivid. Default 1.5.
    """
    value = params.params.get("value", 1.5)
    filterStr = f"eq=saturation={value}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
