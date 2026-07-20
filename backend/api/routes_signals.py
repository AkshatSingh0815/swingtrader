"""Signal and backtest endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.backtest import BacktestResult
from database.models.signal import Signal

router = APIRouter()


@router.get("/signals/latest")
def latest_signals(signal_type: str | None = None, db: Session = Depends(get_db)):
    latest_date = db.query(Signal.date).order_by(desc(Signal.date)).first()
    if not latest_date:
        return []
    q = db.query(Signal).filter(Signal.date == latest_date[0])
    if signal_type:
        q = q.filter(Signal.signal_type == signal_type.upper())
    return q.all()


@router.get("/signals/{symbol}")
def signal_history(symbol: str, limit: int = 30, db: Session = Depends(get_db)):
    return (db.query(Signal).filter(Signal.symbol == symbol.upper())
            .order_by(desc(Signal.date)).limit(limit).all())


@router.get("/backtest/{strategy_name}")
def backtest_results(strategy_name: str, db: Session = Depends(get_db)):
    return (db.query(BacktestResult).filter_by(strategy_name=strategy_name)
            .order_by(desc(BacktestResult.run_date)).all())
