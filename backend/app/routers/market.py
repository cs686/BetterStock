"""Market data endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..schemas import StockQuoteSchema
from ..services.market import DEFAULT_PROVIDER, MarketQuote

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/quotes", response_model=List[StockQuoteSchema])
async def get_quotes() -> List[StockQuoteSchema]:
    quotes = await DEFAULT_PROVIDER.fetch_quotes()
    return [StockQuoteSchema(**quote.__dict__) for quote in quotes]
