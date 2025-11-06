"""Backtesting endpoints."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import BacktestResult, StockQuote
from ..schemas import BacktestResultSchema, BacktestTradeSchema
from ..services.backtest import Backtester, PriceBar

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResultSchema)
async def run_backtest(db: Session = Depends(get_db)) -> BacktestResultSchema:
    backtester = Backtester()
    since = datetime.utcnow() - timedelta(days=60)
    stmt = select(StockQuote).where(StockQuote.updated_at >= since)
    stocks = db.execute(stmt).scalars().all()
    prices: List[PriceBar] = []
    for stock in stocks:
        prices.append(PriceBar(date=stock.updated_at, ticker=stock.ticker, close=stock.price))
    scores = {stock.ticker: stock.percent_change for stock in stocks}
    summary = backtester.run(prices, scores)
    result = BacktestResult(
        strategy_name=summary.strategy_name,
        started_at=summary.started_at,
        ended_at=summary.ended_at,
        total_return=summary.total_return,
        annualized_return=summary.annualized_return,
        max_drawdown=summary.max_drawdown,
        sharpe_ratio=summary.sharpe_ratio,
        trades=[trade.__dict__ for trade in summary.trades],
    )
    db.add(result)
    db.commit()
    return BacktestResultSchema(
        strategy_name=result.strategy_name,
        started_at=result.started_at,
        ended_at=result.ended_at,
        total_return=result.total_return,
        annualized_return=result.annualized_return,
        max_drawdown=result.max_drawdown,
        sharpe_ratio=result.sharpe_ratio,
        trades=[
            BacktestTradeSchema(
                trade_date=trade.trade_date,
                ticker=trade.ticker,
                action=trade.action,
                weight=trade.weight,
            )
            for trade in summary.trades
        ],
    )
