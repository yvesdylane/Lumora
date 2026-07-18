from __future__ import annotations

from pydantic import BaseModel


class WordTiming(BaseModel):
    word: str
    start: float
    end: float


class SubtitleParams(BaseModel):
    words: list[WordTiming]
    fontSize: int = 48
    fontName: str = "Arial"
    primaryColor: str = "&H00FFFFFF"
    outlineColor: str = "&H00000000"
    outlineWidth: int = 2
    position: str = "bottom"
    maxWordsPerLine: int = 6
