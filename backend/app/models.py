"""SQLAlchemy ORM models for BetterStock platform."""
from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String, Table, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

news_stock_association = Table(
    "news_stock_association",
    Base.metadata,
    Column("news_id", ForeignKey("news_articles.id"), primary_key=True),
    Column("ticker", ForeignKey("stock_quotes.ticker"), primary_key=True),
)


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(128), index=True, nullable=False)
    title = Column(String(512), nullable=False)
    url = Column(String(1024), unique=True, nullable=False)
    published_at = Column(DateTime, default=datetime.utcnow)
    summary = Column(String(1024), default="")
    content = Column(Text)
    raw_payload = Column(JSON, default={})

    sentiments = relationship("SentimentScore", back_populates="article", cascade="all, delete-orphan")
    stocks = relationship("StockQuote", secondary=news_stock_association, back_populates="news")


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey("news_articles.id"), nullable=False, index=True)
    provider = Column(String(64), nullable=False)
    sentiment = Column(Float, nullable=False)
    confidence = Column(Float, default=0.0)
    metadata = Column(JSON, default={})

    article = relationship("NewsArticle", back_populates="sentiments")


class StockQuote(Base):
    __tablename__ = "stock_quotes"

    ticker = Column(String(16), primary_key=True)
    name = Column(String(128), nullable=False)
    price = Column(Float, default=0.0)
    change = Column(Float, default=0.0)
    percent_change = Column(Float, default=0.0)
    turnover_rate = Column(Float, default=0.0)
    volume = Column(Float, default=0.0)
    amount = Column(Float, default=0.0)
    industry = Column(String(128), default="Unknown")
    pe_ratio = Column(Float, default=0.0)
    pb_ratio = Column(Float, default=0.0)
    roe = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    news = relationship("NewsArticle", secondary=news_stock_association, back_populates="stocks")
    factors = relationship("IndustryFactor", back_populates="stock", cascade="all, delete-orphan")


class IndustryFactor(Base):
    __tablename__ = "industry_factors"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(16), ForeignKey("stock_quotes.ticker"), index=True)
    factor_name = Column(String(128), index=True)
    value = Column(Float, nullable=False)
    zscore = Column(Float, default=0.0)
    as_of = Column(DateTime, default=datetime.utcnow, index=True)

    stock = relationship("StockQuote", back_populates="factors")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True)
    strategy_name = Column(String(128), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)
    total_return = Column(Float, nullable=False)
    annualized_return = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=False)
    trades = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
