from __future__ import annotations

from pathlib import Path

from models.asset import Asset
from models.effect import EffectParams
from core.media.effects import blur, brightness, contrast, grayscale, saturation, sepia, vignette, sharpen, fade

EFFECTS = {
    "blur": blur.apply,
    "brightness": brightness.apply,
    "contrast": contrast.apply,
    "grayscale": grayscale.apply,
    "saturation": saturation.apply,
    "sepia": sepia.apply,
    "vignette": vignette.apply,
    "sharpen": sharpen.apply,
    "fade": fade.apply,
}


def applyEffect(asset: Asset, effectType: str, params: EffectParams) -> Asset:
    """Apply a video effect by name.

    Looks up effectType in the registry and dispatches to the matching
    effect module's apply() function.

    Args:
        asset: Source video.
        effectType: One of: blur, brightness, contrast, grayscale, saturation,
                    sepia, vignette, sharpen, fade.
        params: Typed effect parameters including params dict, startTime, duration.

    Returns:
        New Asset with the effect applied.

    Raises:
        ValueError: If effectType is not in the registry.
    """
    fn = EFFECTS.get(effectType)
    if fn is None:
        raise ValueError(f"Unknown effect: '{effectType}'. Available: {', '.join(sorted(EFFECTS))}")
    return fn(asset, params)


def applyEffectsPipeline(asset: Asset, effects: list[EffectParams]) -> Asset:
    """Apply multiple effects sequentially to a video.

    Chains each effect: output of effect N becomes input of effect N+1.
    Intermediate files are deleted — only the final output is kept.
    Returns the final Asset with all effects applied.
    """
    current = asset
    for effectParams in effects:
        prev = current
        current = applyEffect(current, effectParams.effectType, effectParams)
        if prev.localPath and prev != asset:
            Path(prev.localPath).unlink(missing_ok=True)
    return current
