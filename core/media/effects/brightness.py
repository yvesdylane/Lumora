from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Adjust video brightness.

    params.params:
        value (float): Brightness adjustment. -1.0 to 1.0. Default 0.1.
    """
    value = params.params.get("value", 0.1)
    filterStr = f"eq=brightness={value}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
