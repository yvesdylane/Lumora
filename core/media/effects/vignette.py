from __future__ import annotations

import math

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Apply a vignette (darkened edges) effect.

    params.params:
        angle (float): Controls vignette spread. Smaller = tighter vignette.
                        Default 0.5 (maps to PI/0.5).
    """
    angle = params.params.get("angle", 0.5)
    filterStr = f"vignette=PI/{angle}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
