"""Stock lookup, latest scan, top-category, and heatmap endpoints."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.indicator import Indicator
from database.models.score import Score
from database.models.stock import PriceHistory, Stock

router = APIRouter()

VALID_CATEGORIES = {
    "swing", "breakout", "momentum", "penny", "dividend",
    "railway", "banking", "defence", "renewable",
}


@router.get("/stocks")
def list_stocks(search: str = "", limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Stock)
    if search:
        q = q.filter(Stock.symbol.ilike(f"%{search.upper()}%") | Stock.name.ilike(f"%{search}%"))
    return q.limit(limit).all()


@router.get("/stocks/{symbol}")
def stock_detail(symbol: str, db: Session = Depends(get_db)):
    stock = db.query(Stock).filter_by(symbol=symbol.upper()).first()
    if not stock:
        raise HTTPException(404, f"Stock {symbol} not found")
    latest_ind = (db.query(Indicator).filter_by(symbol=symbol.upper())
                  .order_by(desc(Indicator.date)).first())
    latest_score = (db.query(Score).filter_by(symbol=symbol.upper())
                    .order_by(desc(Score.date)).first())
    return {"stock": stock, "latest_indicators": latest_ind, "latest_score": latest_score}


@router.get("/stocks/{symbol}/history")
def stock_history(symbol: str, days: int = 250, db: Session = Depends(get_db)):
    cutoff = dt.date.today() - dt.timedelta(days=int(days * 1.6))
    rows = (db.query(PriceHistory).filter(PriceHistory.symbol == symbol.upper(), PriceHistory.date >= cutoff)
            .order_by(PriceHistory.date).all())
    return rows


@router.get("/scans/latest")
def latest_scan(limit: int = 100, min_score: float = 0, db: Session = Depends(get_db)):
    latest_date = db.query(Score.date).order_by(desc(Score.date)).first()
    if not latest_date:
        return []
    q = (db.query(Score).filter(Score.date == latest_date[0], Score.overall_score >= min_score)
         .order_by(Score.rank).limit(limit))
    return q.all()


@router.get("/scans/top/{category}")
def top_by_category(category: str, limit: int = 20, db: Session = Depends(get_db)):
    if category not in VALID_CATEGORIES:
        raise HTTPException(400, f"Unknown category. Valid: {sorted(VALID_CATEGORIES)}")
    latest_date = db.query(Score.date).order_by(desc(Score.date)).first()
    if not latest_date:
        return []
    q = (db.query(Score).filter(Score.date == latest_date[0], Score.category.contains(category))
         .order_by(desc(Score.overall_score)).limit(limit))
    return q.all()


@router.get("/heatmap/{index_name}")
def heatmap(index_name: str, db: Session = Depends(get_db)):
    """Simple sector/stock heatmap data: latest overall_score + implied daily
    change (close vs prior close) per stock, grouped for a treemap-style
    frontend chart. index_name: 'nifty' | 'banknifty'."""
    latest_date = db.query(Score.date).order_by(desc(Score.date)).first()
    if not latest_date:
        return []
    scores = db.query(Score).filter(Score.date == latest_date[0]).all()
    return [{"symbol": s.symbol, "overall_score": s.overall_score, "category": s.category} for s in scores]
