from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Sharpen video using unsharp mask.

    params.params:
        amount (float): Sharpening strength. Default 1.5.
                        Applied to both luma and chroma.
    """
    amount = params.params.get("amount", 1.5)
    filterStr = f"unsharp=5:5:{amount}:5:5:{amount}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
