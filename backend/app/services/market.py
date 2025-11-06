"""Market data providers for BetterStock."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List

import numpy as np

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class MarketQuote:
    ticker: str
    name: str
    price: float
    change: float
    percent_change: float
    turnover_rate: float
    volume: float
    amount: float
    industry: str
    pe_ratio: float
    pb_ratio: float
    roe: float
    updated_at: datetime


class MarketDataProvider:
    async def fetch_quotes(self, tickers: Iterable[str] | None = None) -> List[MarketQuote]:
        raise NotImplementedError


class MockMarketDataProvider(MarketDataProvider):
    """Offline provider generating deterministic synthetic data."""

    def __init__(self) -> None:
        base_time = datetime.utcnow()
        self._quotes = [
            MarketQuote(
                ticker="600519",
                name="贵州茅台",
                price=1600.0,
                change=5.0,
                percent_change=0.3,
                turnover_rate=0.5,
                volume=1.2e6,
                amount=1.9e9,
                industry="白酒",
                pe_ratio=35.0,
                pb_ratio=10.0,
                roe=0.18,
                updated_at=base_time,
            ),
            MarketQuote(
                ticker="000333",
                name="美的集团",
                price=65.0,
                change=-0.5,
                percent_change=-0.76,
                turnover_rate=0.8,
                volume=3.4e6,
                amount=2.2e8,
                industry="家电",
                pe_ratio=18.5,
                pb_ratio=3.4,
                roe=0.15,
                updated_at=base_time,
            ),
            MarketQuote(
                ticker="300750",
                name="宁德时代",
                price=220.0,
                change=2.3,
                percent_change=1.05,
                turnover_rate=1.2,
                volume=5.0e6,
                amount=1.1e9,
                industry="新能源",
                pe_ratio=45.2,
                pb_ratio=5.6,
                roe=0.12,
                updated_at=base_time,
            ),
        ]

    async def fetch_quotes(self, tickers: Iterable[str] | None = None) -> List[MarketQuote]:
        if tickers:
            tickers_set = set(tickers)
            return [quote for quote in self._quotes if quote.ticker in tickers_set]
        return list(self._quotes)


try:  # pragma: no cover - optional dependency
    import akshare as ak  # type: ignore

    class AkshareMarketDataProvider(MarketDataProvider):
        async def fetch_quotes(self, tickers: Iterable[str] | None = None) -> List[MarketQuote]:
            import asyncio

            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, ak.stock_zh_a_spot_em)
            quotes: List[MarketQuote] = []
            for _, row in df.iterrows():
                if tickers and row["代码"] not in tickers:
                    continue
                quotes.append(
                    MarketQuote(
                        ticker=row["代码"],
                        name=row["名称"],
                        price=float(row["最新价"]),
                        change=float(row["涨跌额"]),
                        percent_change=float(row["涨跌幅"]),
                        turnover_rate=float(row.get("换手率", 0) or 0),
                        volume=float(row.get("成交量", 0) or 0),
                        amount=float(row.get("成交额", 0) or 0),
                        industry=str(row.get("所属行业", "未知")),
                        pe_ratio=float(row.get("市盈率", 0) or 0),
                        pb_ratio=float(row.get("市净率", 0) or 0),
                        roe=float(row.get("ROE", 0) or 0),
                        updated_at=datetime.utcnow(),
                    )
                )
            return quotes

    DEFAULT_PROVIDER: MarketDataProvider = AkshareMarketDataProvider()
except Exception:  # pragma: no cover - optional dependency
    logger.warning("Falling back to mock market data provider.")
    DEFAULT_PROVIDER = MockMarketDataProvider()
