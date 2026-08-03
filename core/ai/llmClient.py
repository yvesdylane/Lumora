from __future__ import annotations

import json
import logging
import os
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

DEFAULT_GMI_LLM_MODEL = "openai/gpt-4o-mini"


@runtime_checkable
class LLMClient(Protocol):
    async def complete(self, systemPrompt: str, userPrompt: str) -> str: ...


class GenblazeLLMClient:
    """Real LLM client backed by GMICloud's OpenAI-compatible chat endpoint.

    Auth comes from the ``GMI_API_KEY`` env var (already used by the rest of
    the Genblaze stack). The model id can be overridden with ``GMI_LLM_MODEL``.
    """

    def __init__(
        self,
        model: str | None = None,
        apiKey: str | None = None,
        baseUrl: str | None = None,
    ):
        self.model = model or os.environ.get("GMI_LLM_MODEL", DEFAULT_GMI_LLM_MODEL)
        self.apiKey = apiKey
        self.baseUrl = baseUrl

    async def complete(self, systemPrompt: str, userPrompt: str) -> str:
        from genblaze_gmicloud.chat import achat

        response = await achat(
            model=self.model,
            prompt=userPrompt,
            system=systemPrompt,
            api_key=self.apiKey,
            base_url=self.baseUrl,
        )
        text = (response.text or "").strip()
        if not text:
            raise RuntimeError(
                f"Genblaze LLM returned an empty response for model {self.model}"
            )
        return text


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
