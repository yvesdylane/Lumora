from __future__ import annotations

from core.ai.llmClient import LLMClient
from core.ai.tier0 import (
    generateCaptions as _generateCaptions,
    generateMotionSpec as _generateMotionSpec,
    suggestCutPoints as _suggestCutPoints,
    suggestTransition as _suggestTransition,
)


async def generateCaptions(client: LLMClient, transcript: str, wordTimings: list[dict]) -> dict:
    return await _generateCaptions(client, transcript, wordTimings)


async def suggestTransition(client: LLMClient, clipAMeta: dict, clipBMeta: dict) -> dict:
    return await _suggestTransition(client, clipAMeta, clipBMeta)


async def suggestCutPoints(client: LLMClient, timeline: dict, targetDuration: float) -> list[dict]:
    return await _suggestCutPoints(client, timeline, targetDuration)


async def generateMotionSpec(client: LLMClient, style: str, layerType: str) -> dict:
    return await _generateMotionSpec(client, style, layerType)
