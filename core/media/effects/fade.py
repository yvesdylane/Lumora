from __future__ import annotations

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects.base import applySingleFilter


def apply(asset: Asset, params: EffectParams) -> Asset:
    """Apply fade-in and/or fade-out to video.

    params.params:
        fadeIn (float): Duration of fade-in in seconds. Default 1.0. 0 = no fade-in.
        fadeOut (float): Duration of fade-out in seconds. Default 1.0. 0 = no fade-out.
    """
    fadeIn = params.params.get("fadeIn", 1.0)
    fadeOut = params.params.get("fadeOut", 1.0)

    filters = []
    if fadeIn > 0:
        filters.append(f"fade=t=in:st={params.startTime}:d={fadeIn}")
    if fadeOut > 0:
        fadeOutStart = params.startTime + (params.duration or 0) - fadeOut
        if fadeOutStart < params.startTime:
            fadeOutStart = params.startTime
        filters.append(f"fade=t=out:st={fadeOutStart}:d={fadeOut}")

    if not filters:
        filters.append("fade=t=in:st=0:d=1")

    filterStr = ",".join(filters)
    return applySingleFilter(asset, filterStr, params.startTime, params.duration)
