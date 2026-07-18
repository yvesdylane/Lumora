from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Apply a sepia tone effect.

    Blends a sepia colorchannelmixer with the original using blend.

    params.params:
        strength (float): 0.0 = no effect, 1.0 = full sepia. Default 0.8.
    """
    strength = params.params.get("strength", 0.8)
    sepia = "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131"
    filterStr = f"split[s0][s1];[s0]{sepia}[sepia];[s1][sepia]blend=all_mode=normal:all_opacity={strength}"
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
