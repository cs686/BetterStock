"""Sentiment analysis pipeline built on top of LLM client."""
from __future__ import annotations

import asyncio
from typing import Iterable, List

from .llm import LLMClient, SentimentResult, get_llm_client


class SentimentAnalyzer:
    def __init__(self, client: LLMClient | None = None) -> None:
        self._client = client or get_llm_client()

    async def analyze_batch(self, texts: Iterable[str]) -> List[SentimentResult]:
        tasks = [self._client.analyze(text) for text in texts]
        results = await asyncio.gather(*tasks)
        for result in results:
            result.raw.setdefault("provider", self.provider)
        return results

    async def analyze_text(self, text: str) -> SentimentResult:
        result = await self._client.analyze(text)
        result.raw.setdefault("provider", self.provider)
        return result

    @property
    def provider(self) -> str:
        return getattr(self._client, "provider", "unknown")
