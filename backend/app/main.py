"""FastAPI entrypoint for BetterStock backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from .routers import analytics, backtest, market, news
from .tasks.scheduler import TaskScheduler, initialize_database

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="BetterStock Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news.router)
app.include_router(market.router)
app.include_router(analytics.router)
app.include_router(backtest.router)

initialize_database(engine)
_scheduler: TaskScheduler | None = None


@app.on_event("startup")
async def startup_event() -> None:
    global _scheduler
    _scheduler = TaskScheduler()
    _scheduler.start()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
