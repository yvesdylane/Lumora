import asyncio

from core.ai.agentic import (
    AgenticRun,
    AgenticCheck,
    evaluateDuration,
    evaluateAsrRoundtrip,
    evaluateSilenceClipping,
    runEvaluation,
    decide,
    runAgenticLoop,
)
from models.asset import Asset


def _makeAsset(duration: float | None = None) -> Asset:
    return Asset(
        id="test-asset-id",
        source="ai",
        mimeType="audio/mpeg",
        duration=duration,
    )


async def testEvaluateDuration():
    print("=" * 60)
    print("evaluateDuration")
    print("=" * 60)

    script = "Hello " * 30
    check = evaluateDuration(script, _makeAsset(duration=15.0))

    print(f"  name: {check.name}")
    print(f"  passed: {check.passed}")
    print(f"  score: {check.score:.2f}")
    print(f"  detail: {check.detail}")

    assert check.name == "duration"
    assert check.score > 0
    print("  ✅ Passed")


async def testEvaluateDurationUnknown():
    print("\n" + "=" * 60)
    print("evaluateDuration (unknown duration)")
    print("=" * 60)

    check = evaluateDuration("Hello world", _makeAsset(duration=None))

    print(f"  passed: {check.passed}")
    print(f"  score: {check.score}")
    print(f"  detail: {check.detail}")

    assert check.passed is False
    assert check.score == 0.5
    print("  ✅ Passed")


async def testEvaluateAsrRoundtrip():
    print("\n" + "=" * 60)
    print("evaluateAsrRoundtrip (stub)")
    print("=" * 60)

    check = evaluateAsrRoundtrip("Hello", _makeAsset())

    print(f"  passed: {check.passed}")
    print(f"  score: {check.score}")

    assert check.passed is True
    assert check.score == 1.0
    print("  ✅ Passed")


async def testEvaluateSilenceClipping():
    print("\n" + "=" * 60)
    print("evaluateSilenceClipping (stub)")
    print("=" * 60)

    check = evaluateSilenceClipping(_makeAsset())

    print(f"  passed: {check.passed}")
    print(f"  score: {check.score}")

    assert check.passed is True
    assert check.score == 1.0
    print("  ✅ Passed")


async def testRunEvaluation():
    print("\n" + "=" * 60)
    print("runEvaluation")
    print("=" * 60)

    asset = _makeAsset(duration=12.0)
    run = runEvaluation(asset, {"script": "Hello " * 30})

    print(f"  checks: {len(run.checks)}")
    for c in run.checks:
        print(f"    {c.name}: passed={c.passed} score={c.score:.2f}")
    print(f"  overall score: {run.score:.2f}")

    assert len(run.checks) == 3
    assert 0 <= run.score <= 1
    print("  ✅ Passed")


async def testDecide():
    print("\n" + "=" * 60)
    print("decide")
    print("=" * 60)

    store = decide(AgenticRun(score=0.9))
    retry = decide(AgenticRun(score=0.5))
    escalate = decide(AgenticRun(score=0.2))

    print(f"  score 0.9 → {store}")
    print(f"  score 0.5 → {retry}")
    print(f"  score 0.2 → {escalate}")

    assert store == "store"
    assert retry == "retry"
    assert escalate == "escalate"
    print("  ✅ Passed")


async def testAgenticLoopStoreFirstAttempt():
    print("\n" + "=" * 60)
    print("agenticLoop (store on first attempt)")
    print("=" * 60)

    callCount = 0

    async def mockGenerate(**kwargs):
        nonlocal callCount
        callCount += 1
        return _makeAsset(duration=15.0)

    result = await runAgenticLoop(
        mockGenerate,
        jobArgs={},
        expected={"script": "Hello " * 30},
        maxAttempts=3,
    )

    print(f"  decision: {result.decision}")
    print(f"  attempts: {result.attempts}")
    print(f"  asset: {result.asset.id if result.asset else None}")
    print(f"  calls: {callCount}")

    assert result.decision == "store"
    assert result.attempts == 1
    assert result.asset is not None
    assert callCount == 1
    print("  ✅ Passed")


async def testAgenticLoopRetryThenStore():
    print("\n" + "=" * 60)
    print("agenticLoop (retry then store)")
    print("=" * 60)

    callCount = 0

    async def mockGenerate(**kwargs):
        nonlocal callCount
        callCount += 1
        if callCount == 1:
            return _makeAsset(duration=1.0)
        return _makeAsset(duration=15.0)

    result = await runAgenticLoop(
        mockGenerate,
        jobArgs={},
        expected={"script": "Hello " * 30},
        maxAttempts=3,
    )

    print(f"  decision: {result.decision}")
    print(f"  attempts: {result.attempts}")
    print(f"  calls: {callCount}")

    assert result.decision == "store"
    assert result.attempts == 2
    assert callCount == 2
    print("  ✅ Passed")


async def testAgenticLoopEscalate():
    print("\n" + "=" * 60)
    print("agenticLoop (escalate after max attempts)")
    print("=" * 60)

    async def mockGenerate(**kwargs):
        return _makeAsset(duration=1.0)

    result = await runAgenticLoop(
        mockGenerate,
        jobArgs={},
        expected={"script": "Hello " * 30},
        maxAttempts=3,
    )

    print(f"  decision: {result.decision}")
    print(f"  attempts: {result.attempts}")
    print(f"  runs: {len(result.runs)}")

    assert result.decision == "escalate"
    assert result.attempts == 3
    assert len(result.runs) == 3
    print("  ✅ Passed")


async def testAgenticLoopGenerationError():
    print("\n" + "=" * 60)
    print("agenticLoop (generation error → retry)")
    print("=" * 60)

    callCount = 0

    async def mockGenerate(**kwargs):
        nonlocal callCount
        callCount += 1
        if callCount <= 2:
            raise RuntimeError("Provider rate limit")
        return _makeAsset(duration=15.0)

    result = await runAgenticLoop(
        mockGenerate,
        jobArgs={},
        expected={"script": "Hello " * 30},
        maxAttempts=3,
    )

    print(f"  decision: {result.decision}")
    print(f"  attempts: {result.attempts}")
    print(f"  calls: {callCount}")

    assert result.decision == "store"
    assert result.attempts == 3
    assert callCount == 3
    print("  ✅ Passed")


async def main():
    await testEvaluateDuration()
    await testEvaluateDurationUnknown()
    await testEvaluateAsrRoundtrip()
    await testEvaluateSilenceClipping()
    await testRunEvaluation()
    await testDecide()
    await testAgenticLoopStoreFirstAttempt()
    await testAgenticLoopRetryThenStore()
    await testAgenticLoopEscalate()
    await testAgenticLoopGenerationError()

    print("\n" + "=" * 60)
    print("✅ All agentic tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
