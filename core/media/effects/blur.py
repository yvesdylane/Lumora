from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Apply Gaussian blur to a video.

    params.params:
        sigma (float): Blur strength. Default 5. Higher = more blur.
    """
    sigma = params.params.get("sigma", 5)
    filterStr = f"gblur=sigma={sigma}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
