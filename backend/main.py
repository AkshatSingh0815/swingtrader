"""FastAPI application entrypoint.
Run: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import routes_chat, routes_portfolio, routes_reports, routes_signals, routes_stocks, routes_watchlist
from database.db import init_db
from utils.logger import logger

app = FastAPI(
    title="NSE Swing Trading Platform API",
    description="Daily technical + ML + sentiment scan of NSE stocks for swing trading.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(routes_stocks.router, prefix="/api/v1", tags=["stocks"])
app.include_router(routes_signals.router, prefix="/api/v1", tags=["signals"])
app.include_router(routes_watchlist.router, prefix="/api/v1", tags=["watchlist"])
app.include_router(routes_portfolio.router, prefix="/api/v1", tags=["portfolio"])
app.include_router(routes_chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(routes_reports.router, prefix="/api/v1", tags=["reports"])


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("Database initialized. API ready.")


@app.get("/")
def root() -> dict:
    return {"status": "ok", "service": "NSE Swing Trading Platform API"}


@app.get("/health")
def health() -> dict:
    return {"status": "healthy"}
