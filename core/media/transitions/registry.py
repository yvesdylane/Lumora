from __future__ import annotations

from importlib import import_module

from models.asset import Asset

_TRANSITIONS: dict[str, str] = {
    "fade": "core.media.transitions.fade",
    "fadeblack": "core.media.transitions.fadeblack",
    "wipeleft": "core.media.transitions.wipeleft",
    "wiperight": "core.media.transitions.wiperight",
    "slideleft": "core.media.transitions.slideleft",
    "circleopen": "core.media.transitions.circleopen",
    "dissolve": "core.media.transitions.dissolve",
}


def getAvailableTransitions() -> list[str]:
    return sorted(_TRANSITIONS.keys())


def applyTransition(
    assetA: Asset,
    assetB: Asset,
    transitionType: str,
    duration: float,
    easing: str,
) -> Asset:
    if transitionType not in _TRANSITIONS:
        available = ", ".join(getAvailableTransitions())
        raise ValueError(
            f"Unknown transition '{transitionType}'. Available: {available}"
        )

    module = import_module(_TRANSITIONS[transitionType])
    return module.run(assetA, assetB, duration, easing)
