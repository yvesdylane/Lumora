from __future__ import annotations

from pydantic import BaseModel, Field


class EffectParams(BaseModel):
    effectType: str = Field(..., description="Effect name: blur, brightness, contrast, grayscale, saturation, sepia, vignette, sharpen, fade")
    params: dict = Field(default_factory=dict, description="Effect-specific parameters")
    startTime: float = Field(default=0.0, description="When the effect starts (seconds)")
    duration: float | None = Field(default=None, description="How long the effect lasts. None = full clip duration")
