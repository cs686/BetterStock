"""Comprehensive scoring system combining multiple signals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

import numpy as np


@dataclass(slots=True)
class ScoreComponent:
    name: str
    weight: float
    value: float

    @property
    def contribution(self) -> float:
        return self.weight * self.value


@dataclass(slots=True)
class StockScore:
    ticker: str
    name: str
    components: List[ScoreComponent]

    @property
    def total(self) -> float:
        return float(sum(component.contribution for component in self.components))

    def to_dict(self) -> Dict[str, float]:
        return {component.name: component.contribution for component in self.components}


class ScoreEngine:
    def __init__(self, weights: Dict[str, float] | None = None) -> None:
        self.weights = weights or {
            "sentiment": 0.4,
            "industry": 0.3,
            "technical": 0.2,
            "fundamental": 0.1,
        }

    def score(
        self,
        ticker: str,
        name: str,
        sentiment: float,
        industry_heat: float,
        technical: float,
        fundamental: float,
    ) -> StockScore:
        components = [
            ScoreComponent("sentiment", self.weights["sentiment"], sentiment),
            ScoreComponent("industry", self.weights["industry"], industry_heat),
            ScoreComponent("technical", self.weights["technical"], technical),
            ScoreComponent("fundamental", self.weights["fundamental"], fundamental),
        ]
        return StockScore(ticker=ticker, name=name, components=components)

    def normalize(self, scores: Iterable[StockScore]) -> List[StockScore]:
        scores_list = list(scores)
        if not scores_list:
            return []
        totals = np.array([score.total for score in scores_list])
        min_val, max_val = float(totals.min()), float(totals.max())
        scale = max(max_val - min_val, 1e-6)
        normalized_scores: List[StockScore] = []
        for score in scores_list:
            normalized_total = (score.total - min_val) / scale
            components = [
                ScoreComponent(component.name, component.weight, component.value)
                for component in score.components
            ]
            components.append(ScoreComponent("normalized", 1.0, normalized_total))
            normalized_scores.append(StockScore(score.ticker, score.name, components))
        return normalized_scores
