"""Industry Z-score computation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


@dataclass(slots=True)
class IndustryMetric:
    industry: str
    metric_name: str
    timestamp: datetime
    value: float


@dataclass(slots=True)
class IndustryZScore:
    industry: str
    metric_name: str
    timestamp: datetime
    value: float
    mean: float
    std: float
    zscore: float


class ZScoreCalculator:
    def __init__(self, window: int = 20, min_periods: int | None = None) -> None:
        self.window = window
        self.min_periods = min_periods or max(5, window // 2)

    def compute(self, metrics: Iterable[IndustryMetric]) -> List[IndustryZScore]:
        if not metrics:
            return []
        df = pd.DataFrame([
            {
                "industry": metric.industry,
                "metric": metric.metric_name,
                "timestamp": metric.timestamp,
                "value": metric.value,
            }
            for metric in metrics
        ])
        df = df.sort_values(["industry", "metric", "timestamp"])
        results: List[IndustryZScore] = []
        for (industry, metric_name), group in df.groupby(["industry", "metric"]):
            series = group.set_index("timestamp")["value"].astype(float)
            rolling_mean = series.rolling(window=self.window, min_periods=self.min_periods).mean()
            rolling_std = series.rolling(window=self.window, min_periods=self.min_periods).std(ddof=0)
            zscores = (series - rolling_mean) / rolling_std.replace(0, np.nan)
            for ts, value in series.items():
                zscore = float(zscores.loc[ts]) if not np.isnan(zscores.loc[ts]) else 0.0
                results.append(
                    IndustryZScore(
                        industry=industry,
                        metric_name=metric_name,
                        timestamp=ts,
                        value=float(value),
                        mean=float(rolling_mean.loc[ts]) if not np.isnan(rolling_mean.loc[ts]) else float(value),
                        std=float(rolling_std.loc[ts]) if not np.isnan(rolling_std.loc[ts]) else 1.0,
                        zscore=zscore,
                    )
                )
        return results
