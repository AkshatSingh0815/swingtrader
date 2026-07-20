"""User portfolio holdings."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class PortfolioHolding(Base):
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    buy_price: Mapped[float] = mapped_column(Float)
    buy_date: Mapped[dt.date] = mapped_column(Date)
    current_price: Mapped[float] = mapped_column(Float, default=0.0)
    last_updated: Mapped[dt.date] = mapped_column(Date, default=dt.date.today)

    @property
    def invested(self) -> float:
        return self.quantity * self.buy_price

    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price

    @property
    def pnl(self) -> float:
        return self.current_value - self.invested

    @property
    def pnl_pct(self) -> float:
        return (self.pnl / self.invested * 100) if self.invested else 0.0
