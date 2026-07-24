from __future__ import annotations

from importlib import import_module

from models.asset import Asset

_EFFECTS: dict[str, str] = {
    "blur": "core.media.effects.blur",
    "brightness": "core.media.effects.brightness",
    "contrast": "core.media.effects.contrast",
    "grayscale": "core.media.effects.grayscale",
}


def getAvailableEffects() -> list[str]:
    return sorted(_EFFECTS.keys())


def applyEffect(asset: Asset, filterType: str, params: dict) -> Asset:
    if filterType not in _EFFECTS:
        available = ", ".join(getAvailableEffects())
        raise ValueError(
            f"Unknown effect '{filterType}'. Available: {available}"
        )

    module = import_module(_EFFECTS[filterType])
    return module.run(asset, params)
