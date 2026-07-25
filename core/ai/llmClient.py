from __future__ import annotations

import json
import logging
import os
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class LLMClient(Protocol):
    async def complete(self, systemPrompt: str, userPrompt: str) -> str: ...


class GMIClient:
    def __init__(self, model: str | None = None):
        self._model = model or os.getenv("GMI_MODEL", "google/gemini-3.5-flash-lite")

    async def complete(self, systemPrompt: str, userPrompt: str) -> str:
        from genblaze_gmicloud import achat

        response = await achat(
            model=self._model,
            system=systemPrompt,
            prompt=userPrompt,
        )
        return response.text


class MockLLMClient:
    def __init__(self, responses: dict[str, str | dict] | None = None):
        self._responses: dict[str, str] = {}
        self._calls: list[dict] = []
        if responses:
            for key, val in responses.items():
                self._responses[key] = val if isinstance(val, str) else json.dumps(val)

    async def complete(self, systemPrompt: str, userPrompt: str) -> str:
        self._calls.append({
            "systemPrompt": systemPrompt,
            "userPrompt": userPrompt,
        })

        for key, response in self._responses.items():
            if key.lower() in userPrompt.lower():
                return response

        if self._responses:
            return next(iter(self._responses.values()))

        return json.dumps({"error": "no mock response configured"})

    @property
    def calls(self) -> list[dict]:
        return list(self._calls)
