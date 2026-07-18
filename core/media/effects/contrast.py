from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Adjust video contrast.

    params.params:
        value (float): Contrast multiplier. 0.5 to 2.0. Default 1.3.
    """
    value = params.params.get("value", 1.3)
    filterStr = f"eq=contrast={value}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
