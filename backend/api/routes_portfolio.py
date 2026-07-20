"""Portfolio CRUD + PnL endpoints."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.portfolio import PortfolioHolding
from services.data_fetcher import fetch_history

router = APIRouter()


class HoldingCreate(BaseModel):
    symbol: str
    quantity: int
    buy_price: float
    buy_date: dt.date | None = None


@router.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    holdings = db.query(PortfolioHolding).all()
    total_invested = sum(h.invested for h in holdings)
    total_current = sum(h.current_value for h in holdings)
    return {
        "holdings": holdings,
        "total_invested": round(total_invested, 2),
        "total_current_value": round(total_current, 2),
        "total_pnl": round(total_current - total_invested, 2),
        "total_pnl_pct": round((total_current - total_invested) / total_invested * 100, 2) if total_invested else 0,
    }


@router.post("/portfolio")
def add_holding(item: HoldingCreate, db: Session = Depends(get_db)):
    symbol = item.symbol.upper()
    df = fetch_history(symbol, period="5d")
    current_price = float(df["close"].iloc[-1]) if not df.empty else item.buy_price
    holding = PortfolioHolding(
        symbol=symbol, quantity=item.quantity, buy_price=item.buy_price,
        buy_date=item.buy_date or dt.date.today(), current_price=current_price,
        last_updated=dt.date.today(),
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)  # repopulate attributes SQLAlchemy expired on commit, so the response body isn't empty
    return holding


@router.delete("/portfolio/{holding_id}")
def remove_holding(holding_id: int, db: Session = Depends(get_db)):
    holding = db.query(PortfolioHolding).filter_by(id=holding_id).first()
    if not holding:
        raise HTTPException(404, "Holding not found")
    db.delete(holding)
    db.commit()
    return {"status": "removed", "id": holding_id}
