"""Pydantic schemas for API serialization."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SentimentSchema(BaseModel):
    provider: str
    sentiment: float
    confidence: float
    metadata: dict | None = None

    class Config:
        orm_mode = True


class StockQuoteSchema(BaseModel):
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

    class Config:
        orm_mode = True


class NewsArticleSchema(BaseModel):
    id: int
    source: str
    title: str
    url: str
    published_at: datetime
    summary: str | None = None
    content: str | None = None
    sentiments: List[SentimentSchema] = []
    stocks: List[StockQuoteSchema] = []

    class Config:
        orm_mode = True


class IndustryFactorSchema(BaseModel):
    ticker: str
    factor_name: str
    value: float
    zscore: float
    as_of: datetime

    class Config:
        orm_mode = True


class ScoreResultSchema(BaseModel):
    ticker: str
    name: str
    score: float
    components: dict


class BacktestTradeSchema(BaseModel):
    trade_date: datetime
    ticker: str
    action: str
    weight: float


class BacktestResultSchema(BaseModel):
    strategy_name: str
    started_at: datetime
    ended_at: datetime
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: List[BacktestTradeSchema]

    class Config:
        orm_mode = True
