"""Simple backtesting utilities for ranking-based strategies."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd


@dataclass(slots=True)
class PriceBar:
    date: datetime
    ticker: str
    close: float


@dataclass(slots=True)
class StrategyConfig:
    name: str
    lookback: int = 20
    holding_period: int = 5
    top_k: int = 5


@dataclass(slots=True)
class Trade:
    trade_date: datetime
    ticker: str
    action: str
    weight: float


@dataclass(slots=True)
class BacktestSummary:
    strategy_name: str
    started_at: datetime
    ended_at: datetime
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Trade]


class Backtester:
    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig(name="SentimentRank")

    def run(self, price_history: Iterable[PriceBar], scores: Dict[str, float]) -> BacktestSummary:
        df = pd.DataFrame([
            {"date": bar.date, "ticker": bar.ticker, "close": bar.close}
            for bar in price_history
        ])
        if df.empty:
            now = datetime.utcnow()
            return BacktestSummary(
                strategy_name=self.config.name,
                started_at=now,
                ended_at=now,
                total_return=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                trades=[],
            )
        df = df.pivot(index="date", columns="ticker", values="close").sort_index()
        returns = df.pct_change().fillna(0.0)
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        selected = [ticker for ticker, _ in ranked[: self.config.top_k]]
        if not selected:
            now = datetime.utcnow()
            return BacktestSummary(
                strategy_name=self.config.name,
                started_at=df.index[0],
                ended_at=df.index[-1],
                total_return=0.0,
                annualized_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                trades=[],
            )
        portfolio_returns = returns[selected].mean(axis=1)
        cumulative = (1 + portfolio_returns).cumprod()
        total_return = float(cumulative.iloc[-1] - 1)
        annualized_return = (1 + total_return) ** (252 / max(len(cumulative), 1)) - 1
        drawdown = cumulative / cumulative.cummax() - 1
        max_drawdown = float(drawdown.min())
        sharpe_ratio = float((portfolio_returns.mean() / (portfolio_returns.std(ddof=0) + 1e-6)) * np.sqrt(252))
        trades = [
            Trade(trade_date=df.index[-1], ticker=ticker, action="buy", weight=1 / self.config.top_k)
            for ticker in selected
        ]
        return BacktestSummary(
            strategy_name=self.config.name,
            started_at=df.index[0],
            ended_at=df.index[-1],
            total_return=total_return,
            annualized_return=float(annualized_return),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
        )
