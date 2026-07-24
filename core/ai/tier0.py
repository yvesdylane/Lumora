from __future__ import annotations

import json
import logging

from core.ai.llmClient import LLMClient

logger = logging.getLogger(__name__)


async def generateCaptions(
    client: LLMClient,
    transcript: str,
    wordTimings: list[dict],
) -> dict:
    systemPrompt = (
        "You are a subtitle designer for a video editor. "
        "Given a transcript and word timings, generate styled caption params. "
        "Return ONLY valid JSON matching the schema."
    )

    userPrompt = (
        f"Transcript:\n{transcript}\n\n"
        f"Word timings ({len(wordTimings)} words):\n"
        f"{json.dumps(wordTimings[:20], indent=2)}"
        f"{'...' if len(wordTimings) > 20 else ''}\n\n"
        "Return a JSON object with:\n"
        '- "text": the full caption text\n'
        '- "font": font name (default "Arial")\n'
        '- "size": font size (default 48)\n'
        '- "color": text color (default "white")\n'
        '- "bgColor": background color (null for transparent)\n'
        '- "position": {"x": 0.5, "y": 0.9}\n'
        '- "startTime": start time in seconds from first word\n'
        '- "duration": total duration of all words'
    )

    raw = await client.complete(systemPrompt, userPrompt)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("generateCaptions: LLM returned invalid JSON, using defaults")
        result = {}

    return {
        "text": result.get("text", transcript),
        "font": result.get("font", "Arial"),
        "size": result.get("size", 48),
        "color": result.get("color", "white"),
        "bgColor": result.get("bgColor"),
        "position": result.get("position", {"x": 0.5, "y": 0.9}),
        "startTime": result.get("startTime", 0.0),
        "duration": result.get("duration"),
    }


async def suggestTransition(
    client: LLMClient,
    clipAMeta: dict,
    clipBMeta: dict,
) -> dict:
    systemPrompt = (
        "You are a video editing assistant. "
        "Given metadata for two adjacent clips, suggest the best transition. "
        "Return ONLY valid JSON matching the schema."
    )

    userPrompt = (
        f"Clip A metadata:\n{json.dumps(clipAMeta, indent=2)}\n\n"
        f"Clip B metadata:\n{json.dumps(clipBMeta, indent=2)}\n\n"
        "Return a JSON object with:\n"
        '- "type": transition type ("fade", "dissolve", "slideLeft", "wipeLeft", '
        '"wipeRight", "circleOpen", "fadeBlack")\n'
        '- "duration": transition duration in seconds (0.5-2.0)\n'
        '- "easing": easing function ("linear", "easeIn", "easeOut", "easeInOut")'
    )

    raw = await client.complete(systemPrompt, userPrompt)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("suggestTransition: LLM returned invalid JSON, using defaults")
        result = {}

    validTypes = {
        "fade", "dissolve", "slideLeft", "wipeLeft",
        "wipeRight", "circleOpen", "fadeBlack",
    }
    transitionType = result.get("type", "fade")
    if transitionType not in validTypes:
        transitionType = "fade"

    return {
        "type": transitionType,
        "duration": max(0.5, min(2.0, result.get("duration", 1.0))),
        "easing": result.get("easing", "linear"),
    }


async def suggestCutPoints(
    client: LLMClient,
    timeline: dict,
    targetDuration: float,
) -> list[dict]:
    systemPrompt = (
        "You are a video editing assistant. "
        "Given a timeline's layer summary and a target duration, "
        "suggest cut points to trim the timeline to the target. "
        "Return ONLY valid JSON matching the schema."
    )

    userPrompt = (
        f"Timeline layers:\n{json.dumps(timeline, indent=2)}\n\n"
        f"Target duration: {targetDuration}s\n\n"
        "Return a JSON array of cut point objects:\n"
        '- "position": time in seconds to cut\n'
        '- "reason": why this cut point was chosen\n'
        '- "confidence": 0.0-1.0 how confident you are'
    )

    raw = await client.complete(systemPrompt, userPrompt)

    try:
        result = json.loads(raw)
        if not isinstance(result, list):
            result = []
    except json.JSONDecodeError:
        logger.warning("suggestCutPoints: LLM returned invalid JSON, returning empty")
        result = []

    validated = []
    for point in result:
        if isinstance(point, dict) and "position" in point:
            validated.append({
                "position": float(point["position"]),
                "reason": point.get("reason", ""),
                "confidence": max(0.0, min(1.0, float(point.get("confidence", 0.5)))),
            })

    return validated


async def generateMotionSpec(
    client: LLMClient,
    style: str,
    layerType: str,
) -> dict:
    systemPrompt = (
        "You are a motion design assistant for a video editor. "
        "Given a visual style and layer type, generate an animation spec. "
        "Return ONLY valid JSON matching the schema."
    )

    userPrompt = (
        f"Style: {style}\n"
        f"Layer type: {layerType}\n\n"
        "Return a JSON object with:\n"
        '- "keyframes": array of {time: float (0.0-1.0), props: {opacity, scale, x, y, rotation}}\n'
        '- "easing": easing function for the overall animation\n'
        '- "duration": animation duration in seconds'
    )

    raw = await client.complete(systemPrompt, userPrompt)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("generateMotionSpec: LLM returned invalid JSON, using defaults")
        result = {}

    keyframes = []
    for kf in result.get("keyframes", []):
        if isinstance(kf, dict) and "time" in kf:
            keyframes.append({
                "time": max(0.0, min(1.0, float(kf["time"]))),
                "props": kf.get("props", {}),
            })

    if not keyframes:
        keyframes = [
            {"time": 0.0, "props": {"opacity": 0.0, "scale": 1.0}},
            {"time": 1.0, "props": {"opacity": 1.0, "scale": 1.0}},
        ]

    return {
        "keyframes": keyframes,
        "easing": result.get("easing", "linear"),
        "duration": result.get("duration", 1.0),
    }
