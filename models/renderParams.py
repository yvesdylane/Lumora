from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator


class ClipParams(BaseModel):
    assetId: str
    start: float = 0.0
    end: float | None = None


class TransitionParams(BaseModel):
    type: str
    duration: float = 1.0
    easing: str = "linear"


class AudioParams(BaseModel):
    assetId: str
    volume: float = 1.0
    fadeIn: float = 0.0
    fadeOut: float = 0.0
    startTime: float = 0.0


class TextParams(BaseModel):
    text: str = ""
    content: str | None = None
    font: str = "Arial"
    fontFamily: str | None = None
    size: int = 48
    color: str = "white"
    bgColor: str | None = None
    position: dict = {"x": 0.5, "y": 0.9}
    startTime: float = 0.0
    duration: float | None = None
    outlineWidth: int = 0
    outlineColor: str = "black"
    shadowX: float = 0.0
    shadowY: float = 0.0
    shadowColor: str = "black"
    box: bool = False
    boxColor: str = "black"
    boxBorderW: int = 8
    rotation: float = 0.0
    opacity: float = 1.0

    @model_validator(mode="before")
    @classmethod
    def _aliasContentToText(cls, data):
        if isinstance(data, dict):
            text = data.get("text")
            content = data.get("content")
            if (text is None or text == "") and content is not None:
                return {**data, "text": content}
        return data


class EffectParams(BaseModel):
    filterType: str


class BlurParams(EffectParams):
    filterType: Literal["blur"] = "blur"
    strength: int = 5


class BrightnessParams(EffectParams):
    filterType: Literal["brightness"] = "brightness"
    factor: float = 1.2


class ContrastParams(EffectParams):
    filterType: Literal["contrast"] = "contrast"
    factor: float = 1.3


class GrayscaleParams(EffectParams):
    filterType: Literal["grayscale"] = "grayscale"


EFFECT_PARAM_MAP: dict[str, type[EffectParams]] = {
    "blur": BlurParams,
    "brightness": BrightnessParams,
    "contrast": ContrastParams,
    "grayscale": GrayscaleParams,
}


class LayerComposition(BaseModel):
    layerType: str
    params: dict
    source: str = "manual"
    position: int = 0


class TrackComposition(BaseModel):
    kind: str
    position: int = 0
    layers: list[LayerComposition] = []


class TimelineComposition(BaseModel):
    tracks: list[TrackComposition] = []
