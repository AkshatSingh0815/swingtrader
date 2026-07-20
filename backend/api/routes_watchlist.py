"""Watchlist CRUD endpoints."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.watchlist import WatchlistItem

router = APIRouter()


class WatchlistCreate(BaseModel):
    symbol: str
    notes: str = ""


@router.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    return db.query(WatchlistItem).all()


@router.post("/watchlist")
def add_to_watchlist(item: WatchlistCreate, db: Session = Depends(get_db)):
    symbol = item.symbol.upper()
    if db.query(WatchlistItem).filter_by(symbol=symbol).first():
        raise HTTPException(400, f"{symbol} already in watchlist")
    wl = WatchlistItem(symbol=symbol, added_date=dt.date.today(), notes=item.notes)
    db.add(wl)
    db.commit()
    db.refresh(wl)  # repopulate attributes SQLAlchemy expired on commit, so the response body isn't empty
    return wl


@router.delete("/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    wl = db.query(WatchlistItem).filter_by(symbol=symbol.upper()).first()
    if not wl:
        raise HTTPException(404, "Not found in watchlist")
    db.delete(wl)
    db.commit()
    return {"status": "removed", "symbol": symbol.upper()}
