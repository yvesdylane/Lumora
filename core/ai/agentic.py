from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Literal

from models.asset import Asset

logger = logging.getLogger(__name__)

WORDS_PER_MINUTE = 150
STORE_THRESHOLD = 0.8
RETRY_THRESHOLD = 0.4


@dataclass
class AgenticCheck:
    name: str
    passed: bool
    score: float
    detail: str = ""


@dataclass
class AgenticRun:
    checks: list[AgenticCheck] = field(default_factory=list)
    score: float = 0.0
    decision: Literal["store", "retry", "escalate"] = "retry"


@dataclass
class AgenticResult:
    asset: Asset | None
    decision: Literal["store", "retry", "escalate"]
    attempts: int
    runs: list[AgenticRun]
    error: str | None = None


def evaluateDuration(script: str, candidate: Asset) -> AgenticCheck:
    wordCount = len(script.split())
    expectedSeconds = (wordCount / WORDS_PER_MINUTE) * 60

    if candidate.duration is None:
        return AgenticCheck(
            name="duration",
            passed=False,
            score=0.5,
            detail="duration unknown, cannot validate",
        )

    ratio = candidate.duration / expectedSeconds if expectedSeconds > 0 else 1.0
    score = max(0.0, 1.0 - abs(1.0 - ratio))
    passed = 0.5 <= ratio <= 2.0

    return AgenticCheck(
        name="duration",
        passed=passed,
        score=score,
        detail=f"expected ~{expectedSeconds:.1f}s, got {candidate.duration:.1f}s (ratio={ratio:.2f})",
    )


def evaluateAsrRoundtrip(script: str, candidate: Asset) -> AgenticCheck:
    return AgenticCheck(
        name="asr_roundtrip",
        passed=True,
        score=1.0,
        detail="stub — ASR not implemented yet",
    )


def evaluateSilenceClipping(candidate: Asset) -> AgenticCheck:
    return AgenticCheck(
        name="silence_clipping",
        passed=True,
        score=1.0,
        detail="stub — silence detection not implemented yet",
    )


def runEvaluation(candidate: Asset, expected: dict | None = None) -> AgenticRun:
    script = expected.get("script", "") if expected else ""

    checks = [
        evaluateDuration(script, candidate),
        evaluateAsrRoundtrip(script, candidate),
        evaluateSilenceClipping(candidate),
    ]

    avgScore = sum(c.score for c in checks) / len(checks) if checks else 0.0

    return AgenticRun(checks=checks, score=avgScore)


def decide(run: AgenticRun) -> Literal["store", "retry", "escalate"]:
    if run.score >= STORE_THRESHOLD:
        return "store"
    if run.score >= RETRY_THRESHOLD:
        return "retry"
    return "escalate"


async def runAgenticLoop(
    generateFn: Callable[..., Asset],
    jobArgs: dict,
    expected: dict | None = None,
    maxAttempts: int = 3,
) -> AgenticResult:
    runs: list[AgenticRun] = []
    lastAsset: Asset | None = None
    lastError: str | None = None

    for attempt in range(1, maxAttempts + 1):
        logger.info(f"agentic attempt {attempt}/{maxAttempts}")

        try:
            asset = await generateFn(**jobArgs)
            lastAsset = asset
        except Exception as e:
            logger.warning(f"agentic attempt {attempt} generation failed: {e}")
            lastError = str(e)
            run = AgenticRun(
                checks=[AgenticCheck(name="generation", passed=False, score=0.0, detail=str(e))],
                score=0.0,
                decision="retry",
            )
            runs.append(run)
            continue

        run = runEvaluation(asset, expected)
        decision = decide(run)
        run.decision = decision
        runs.append(run)

        logger.info(f"agentic attempt {attempt}: score={run.score:.2f} decision={decision}")

        if decision == "store":
            return AgenticResult(
                asset=asset,
                decision="store",
                attempts=attempt,
                runs=runs,
            )

    return AgenticResult(
        asset=lastAsset,
        decision="escalate",
        attempts=maxAttempts,
        runs=runs,
        error=lastError,
    )
