import asyncio
import json

from core.ai.llmClient import MockLLMClient
from core.ai.tier0 import (
    generateCaptions,
    suggestTransition,
    suggestCutPoints,
    generateMotionSpec,
)


async def testGenerateCaptions():
    print("=" * 60)
    print("generateCaptions")
    print("=" * 60)

    mock = MockLLMClient({
        "caption": {
            "text": "Welcome to Lumora",
            "font": "Helvetica",
            "size": 56,
            "color": "yellow",
            "bgColor": "black",
            "position": {"x": 0.5, "y": 0.85},
            "startTime": 0.5,
            "duration": 3.2,
        }
    })

    wordTimings = [
        {"word": "Welcome", "start": 0.5, "end": 1.0},
        {"word": "to", "start": 1.0, "end": 1.2},
        {"word": "Lumora", "start": 1.2, "end": 1.8},
    ]

    result = await generateCaptions(
        mock,
        "Welcome to Lumora",
        wordTimings,
    )

    print(f"  text: {result['text']}")
    print(f"  font: {result['font']}")
    print(f"  size: {result['size']}")
    print(f"  color: {result['color']}")
    print(f"  bgColor: {result['bgColor']}")
    print(f"  position: {result['position']}")
    print(f"  startTime: {result['startTime']}")
    print(f"  duration: {result['duration']}")

    assert result["text"] == "Welcome to Lumora"
    assert result["font"] == "Helvetica"
    assert result["size"] == 56
    assert result["color"] == "yellow"
    assert result["bgColor"] == "black"
    assert result["position"] == {"x": 0.5, "y": 0.85}
    assert result["startTime"] == 0.5
    assert result["duration"] == 3.2

    assert len(mock.calls) == 1
    print("  ✅ Passed")


async def testGenerateCaptionsFallback():
    print("\n" + "=" * 60)
    print("generateCaptions (invalid JSON fallback)")
    print("=" * 60)

    mock = MockLLMClient({"caption": "not json at all"})

    result = await generateCaptions(mock, "Hello world", [])
    print(f"  text: {result['text']}")
    print(f"  font: {result['font']}")

    assert result["text"] == "Hello world"
    assert result["font"] == "Arial"
    print("  ✅ Passed")


async def testSuggestTransition():
    print("\n" + "=" * 60)
    print("suggestTransition")
    print("=" * 60)

    mock = MockLLMClient({
        "transition": {
            "type": "dissolve",
            "duration": 1.5,
            "easing": "easeInOut",
        }
    })

    clipA = {"duration": 10.0, "type": "video", "resolution": "1920x1080"}
    clipB = {"duration": 8.0, "type": "video", "resolution": "1920x1080"}

    result = await suggestTransition(mock, clipA, clipB)

    print(f"  type: {result['type']}")
    print(f"  duration: {result['duration']}")
    print(f"  easing: {result['easing']}")

    assert result["type"] == "dissolve"
    assert result["duration"] == 1.5
    assert result["easing"] == "easeInOut"
    print("  ✅ Passed")


async def testSuggestTransitionFallback():
    print("\n" + "=" * 60)
    print("suggestTransition (invalid type fallback)")
    print("=" * 60)

    mock = MockLLMClient({
        "transition": {
            "type": "invalidType",
            "duration": 1.0,
            "easing": "linear",
        }
    })

    result = await suggestTransition(mock, {}, {})
    print(f"  type: {result['type']} (expected: fade)")

    assert result["type"] == "fade"
    print("  ✅ Passed")


async def testSuggestTransitionDurationClamp():
    print("\n" + "=" * 60)
    print("suggestTransition (duration clamp)")
    print("=" * 60)

    mock = MockLLMClient({
        "transition": {
            "type": "fade",
            "duration": 5.0,
            "easing": "linear",
        }
    })

    result = await suggestTransition(mock, {}, {})
    print(f"  duration: {result['duration']} (expected: 2.0, clamped)")

    assert result["duration"] == 2.0

    mock2 = MockLLMClient({
        "transition": {
            "type": "fade",
            "duration": 0.1,
            "easing": "linear",
        }
    })

    result2 = await suggestTransition(mock2, {}, {})
    print(f"  duration: {result2['duration']} (expected: 0.5, clamped)")
    assert result2["duration"] == 0.5
    print("  ✅ Passed")


async def testSuggestCutPoints():
    print("\n" + "=" * 60)
    print("suggestCutPoints")
    print("=" * 60)

    mock = MockLLMClient({
        "cut_points": [
            {"position": 5.0, "reason": "Scene transition", "confidence": 0.9},
            {"position": 12.0, "reason": "End of dialogue", "confidence": 0.7},
        ]
    })

    timeline = {
        "layers": [
            {"type": "clip", "start": 0, "end": 20},
            {"type": "audio", "start": 0, "end": 20},
        ]
    }

    result = await suggestCutPoints(mock, timeline, targetDuration=15.0)

    print(f"  cut points: {len(result)}")
    for cp in result:
        print(f"    position={cp['position']} reason={cp['reason']} confidence={cp['confidence']}")

    assert len(result) == 2
    assert result[0]["position"] == 5.0
    assert result[0]["confidence"] == 0.9
    assert result[1]["position"] == 12.0
    print("  ✅ Passed")


async def testSuggestCutPointsEmpty():
    print("\n" + "=" * 60)
    print("suggestCutPoints (empty/invalid response)")
    print("=" * 60)

    mock = MockLLMClient({"cut": "not valid json"})

    result = await suggestCutPoints(mock, {}, targetDuration=10.0)
    print(f"  cut points: {len(result)} (expected: 0)")

    assert len(result) == 0
    print("  ✅ Passed")


async def testGenerateMotionSpec():
    print("\n" + "=" * 60)
    print("generateMotionSpec")
    print("=" * 60)

    mock = MockLLMClient({
        "motion": {
            "keyframes": [
                {"time": 0.0, "props": {"opacity": 0.0, "scale": 0.8, "y": 20}},
                {"time": 0.5, "props": {"opacity": 1.0, "scale": 1.0, "y": 0}},
                {"time": 1.0, "props": {"opacity": 1.0, "scale": 1.0, "y": 0}},
            ],
            "easing": "easeOut",
            "duration": 2.0,
        }
    })

    result = await generateMotionSpec(mock, "cinematic", "text")

    print(f"  keyframes: {len(result['keyframes'])}")
    for kf in result["keyframes"]:
        print(f"    time={kf['time']} props={kf['props']}")
    print(f"  easing: {result['easing']}")
    print(f"  duration: {result['duration']}")

    assert len(result["keyframes"]) == 3
    assert result["keyframes"][0]["time"] == 0.0
    assert result["keyframes"][0]["props"]["opacity"] == 0.0
    assert result["keyframes"][2]["time"] == 1.0
    assert result["easing"] == "easeOut"
    assert result["duration"] == 2.0
    print("  ✅ Passed")


async def testGenerateMotionSpecFallback():
    print("\n" + "=" * 60)
    print("generateMotionSpec (empty keyframes fallback)")
    print("=" * 60)

    mock = MockLLMClient({"motion": "bad json"})

    result = await generateMotionSpec(mock, "vlog", "image")

    print(f"  keyframes: {len(result['keyframes'])} (expected: 2 default)")
    print(f"  easing: {result['easing']}")
    print(f"  duration: {result['duration']}")

    assert len(result["keyframes"]) == 2
    assert result["keyframes"][0]["props"]["opacity"] == 0.0
    assert result["keyframes"][1]["props"]["opacity"] == 1.0
    print("  ✅ Passed")


async def main():
    await testGenerateCaptions()
    await testGenerateCaptionsFallback()
    await testSuggestTransition()
    await testSuggestTransitionFallback()
    await testSuggestTransitionDurationClamp()
    await testSuggestCutPoints()
    await testSuggestCutPointsEmpty()
    await testGenerateMotionSpec()
    await testGenerateMotionSpecFallback()

    print("\n" + "=" * 60)
    print("✅ All tier0 tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
