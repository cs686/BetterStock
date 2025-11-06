"""Analytics endpoints covering scoring and industry z-score."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import IndustryFactor, NewsArticle, SentimentScore, StockQuote
from ..schemas import IndustryFactorSchema, ScoreResultSchema
from ..services.scoring import ScoreEngine
from ..services.zscore import IndustryMetric, ZScoreCalculator

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/scores", response_model=List[ScoreResultSchema])
async def get_scores(db: Session = Depends(get_db)) -> List[ScoreResultSchema]:
    score_engine = ScoreEngine()
    stmt = select(StockQuote)
    stocks = db.execute(stmt).scalars().all()
    scores = []
    for stock in stocks:
        sentiment_value = 0.0
        if stock.news:
            sentiments = [s.sentiment for article in stock.news for s in article.sentiments]
            if sentiments:
                sentiment_value = float(sum(sentiments) / len(sentiments))
        industry_factor = (
            db.query(IndustryFactor)
            .filter(IndustryFactor.ticker == f"industry::{stock.industry}")
            .order_by(IndustryFactor.as_of.desc())
            .first()
        )
        industry_value = industry_factor.zscore if industry_factor else 0.0
        technical = stock.percent_change / 100
        fundamental = 0.5
        if hasattr(stock, "pe_ratio") and getattr(stock, "pe_ratio"):
            fundamental = min(2.0, 1.0 / float(getattr(stock, "pe_ratio")))
        stock_score = score_engine.score(
            ticker=stock.ticker,
            name=stock.name,
            sentiment=sentiment_value,
            industry_heat=industry_value,
            technical=technical,
            fundamental=fundamental,
        )
        scores.append(stock_score)
    normalized = score_engine.normalize(scores)
    return [
        ScoreResultSchema(
            ticker=score.ticker,
            name=score.name,
            score=score.to_dict().get("normalized", score.total),
            components=score.to_dict(),
        )
        for score in normalized
    ]


@router.post("/industry/zscore", response_model=List[IndustryFactorSchema])
async def compute_industry_zscore(db: Session = Depends(get_db)) -> List[IndustryFactorSchema]:
    calculator = ZScoreCalculator(window=20)
    metrics: List[IndustryMetric] = []
    since = datetime.utcnow() - timedelta(days=60)
    stmt = select(StockQuote).where(StockQuote.updated_at >= since)
    stocks = db.execute(stmt).scalars().all()
    for stock in stocks:
        metrics.append(
            IndustryMetric(
                industry=stock.industry,
                metric_name="turnover",
                timestamp=stock.updated_at,
                value=stock.turnover_rate,
            )
        )
        metrics.append(
            IndustryMetric(
                industry=stock.industry,
                metric_name="sentiment",
                timestamp=stock.updated_at,
                value=stock.percent_change,
            )
        )
    results = calculator.compute(metrics)
    db.query(IndustryFactor).delete()
    for result in results:
        db.add(
            IndustryFactor(
                ticker="industry::" + result.industry,
                factor_name=f"{result.metric_name}_z",
                value=result.value,
                zscore=result.zscore,
                as_of=result.timestamp,
            )
        )
    db.commit()
    return [
        IndustryFactorSchema(
            ticker="industry::" + res.industry,
            factor_name=f"{res.metric_name}_z",
            value=res.value,
            zscore=res.zscore,
            as_of=res.timestamp,
        )
        for res in results
    ]
