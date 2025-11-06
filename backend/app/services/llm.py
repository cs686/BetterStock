"""Large language model integration helpers."""
from __future__ import annotations

import abc
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    sentiment: float
    confidence: float
    raw: Dict[str, Any]


class LLMClient(abc.ABC):
    """Abstract base class for LLM providers."""

    provider: str

    @abc.abstractmethod
    async def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment for the provided text."""


class HeuristicLLMClient(LLMClient):
    """Fallback client that mimics LLM behaviour via heuristics."""

    provider = "heuristic"

    POSITIVE_KEYWORDS = {"增长", "盈利", "创新", "突破", "上升", "盈利"}
    NEGATIVE_KEYWORDS = {"下跌", "亏损", "风险", "下滑", "裁员", "震荡"}

    async def analyze(self, text: str) -> SentimentResult:
        text_lower = text.lower()
        pos_hits = sum(1 for word in self.POSITIVE_KEYWORDS if word in text_lower)
        neg_hits = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text_lower)
        score = 0.0
        if pos_hits or neg_hits:
            score = (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)
        confidence = min(1.0, 0.3 + 0.1 * (pos_hits + neg_hits))
        return SentimentResult(sentiment=score, confidence=confidence, raw={"pos": pos_hits, "neg": neg_hits})


class OpenAIChatClient(LLMClient):
    """Example OpenAI client implementation."""

    provider = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        try:
            import openai  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("openai package is required for OpenAIChatClient") from exc
        self._client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = model

    async def analyze(self, text: str) -> SentimentResult:  # pragma: no cover - network usage
        response = await self._client.responses.create(
            model=self._model,
            input=[
                {
                    "role": "system",
                    "content": "You are a financial analyst rating sentiment between -1 and 1.",
                },
                {
                    "role": "user",
                    "content": f"请对以下新闻进行情感分析, 返回json格式{{'sentiment':-1到1,'confidence':0到1}}: {text}",
                },
            ],
        )
        data = response.output[0].content[0].text  # type: ignore[attr-defined]
        try:
            payload = eval(data)  # noqa: S307 - expecting trusted model output
        except Exception:  # pragma: no cover - depends on LLM output
            logger.exception("Failed to parse LLM response: %s", data)
            raise
        return SentimentResult(
            sentiment=float(payload.get("sentiment", 0.0)),
            confidence=float(payload.get("confidence", 0.0)),
            raw=payload,
        )


def get_llm_client() -> LLMClient:
    provider = os.getenv("BETTERSTOCK_LLM_PROVIDER", "heuristic")
    if provider == "openai":
        return OpenAIChatClient()
    return HeuristicLLMClient()
