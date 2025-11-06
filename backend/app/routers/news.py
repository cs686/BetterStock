"""News related API endpoints."""
from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models import NewsArticle, SentimentScore
from ..schemas import NewsArticleSchema
from ..services.crawler import fetch_latest_news
from ..services.sentiment import SentimentAnalyzer

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/latest", response_model=List[NewsArticleSchema])
async def latest_news(limit: int = 20, db: Session = Depends(get_db)) -> List[NewsArticleSchema]:
    stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit)
    articles = db.execute(stmt).scalars().unique().all()
    return [NewsArticleSchema.from_orm(article) for article in articles]


@router.post("/refresh", response_model=int)
async def refresh_news(db: Session = Depends(get_db)) -> int:
    items = await fetch_latest_news()
    analyzer = SentimentAnalyzer()
    for item in items:
        article = db.query(NewsArticle).filter_by(url=item.url).one_or_none()
        if article:
            continue
        article = NewsArticle(
            source=item.source,
            title=item.title,
            url=item.url,
            published_at=item.published_at,
            summary=item.summary,
            content=item.content,
            raw_payload=item.payload,
        )
        db.add(article)
        db.flush()
        result = await analyzer.analyze_text(item.content or item.summary)
        db.add(
            SentimentScore(
                article_id=article.id,
                provider=analyzer.provider,
                sentiment=result.sentiment,
                confidence=result.confidence,
                metadata=result.raw,
            )
        )
    db.commit()
    return len(items)
