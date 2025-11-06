"""Application-wide scheduler setup using APScheduler."""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from ..database import session_scope
from ..models import Base, NewsArticle, SentimentScore, StockQuote
from ..services.crawler import fetch_latest_news
from ..services.market import DEFAULT_PROVIDER
from ..services.sentiment import SentimentAnalyzer

logger = logging.getLogger(__name__)


class TaskScheduler:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
        self._sentiment = SentimentAnalyzer()

    def start(self) -> None:
        self._scheduler.add_job(self.refresh_news, "interval", minutes=60, id="refresh_news")
        self._scheduler.add_job(self.refresh_market, "interval", minutes=5, id="refresh_market")
        self._scheduler.start()

    async def refresh_news(self) -> None:
        logger.info("Refreshing news feed...")
        items = await fetch_latest_news()
        if not items:
            return
        async def process_item(item):
            result = await self._sentiment.analyze_text(item.content or item.summary)
            with session_scope() as session:
                existing = session.query(NewsArticle).filter_by(url=item.url).one_or_none()
                if existing:
                    return
                article = NewsArticle(
                    source=item.source,
                    title=item.title,
                    url=item.url,
                    published_at=item.published_at,
                    summary=item.summary,
                    content=item.content,
                    raw_payload=item.payload,
                )
                session.add(article)
                session.flush()
                session.add(
                    SentimentScore(
                        article_id=article.id,
                        provider=result.raw.get("provider", "heuristic"),
                        sentiment=result.sentiment,
                        confidence=result.confidence,
                        metadata=result.raw,
                    )
                )
        await asyncio.gather(*(process_item(item) for item in items))

    async def refresh_market(self) -> None:
        logger.info("Refreshing market data...")
        quotes = await DEFAULT_PROVIDER.fetch_quotes()
        with session_scope() as session:
            for quote in quotes:
                existing = session.get(StockQuote, quote.ticker)
                if existing:
                    existing.price = quote.price
                    existing.change = quote.change
                    existing.percent_change = quote.percent_change
                    existing.turnover_rate = quote.turnover_rate
                    existing.volume = quote.volume
                    existing.amount = quote.amount
                    existing.industry = quote.industry
                    existing.pe_ratio = quote.pe_ratio
                    existing.pb_ratio = quote.pb_ratio
                    existing.roe = quote.roe
                    existing.updated_at = quote.updated_at
                else:
                    session.add(
                        StockQuote(
                            ticker=quote.ticker,
                            name=quote.name,
                            price=quote.price,
                            change=quote.change,
                            percent_change=quote.percent_change,
                            turnover_rate=quote.turnover_rate,
                            volume=quote.volume,
                            amount=quote.amount,
                            industry=quote.industry,
                            pe_ratio=quote.pe_ratio,
                            pb_ratio=quote.pb_ratio,
                            roe=quote.roe,
                            updated_at=quote.updated_at,
                        )
                    )


def initialize_database(engine) -> None:
    Base.metadata.create_all(bind=engine)
