"""BUY/SELL/HOLD signals with full risk-management plan."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Date, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    signal_type: Mapped[str] = mapped_column(String(16))  # BUY | SELL | HOLD | STRONG_BUY
    entry: Mapped[float] = mapped_column(Float, default=0.0)
    stop_loss: Mapped[float] = mapped_column(Float, default=0.0)
    target_1: Mapped[float] = mapped_column(Float, default=0.0)
    target_2: Mapped[float] = mapped_column(Float, default=0.0)
    target_3: Mapped[float] = mapped_column(Float, default=0.0)
    position_size: Mapped[int] = mapped_column(Integer, default=0)
    risk_pct: Mapped[float] = mapped_column(Float, default=0.0)
    capital_allocated: Mapped[float] = mapped_column(Float, default=0.0)
    risk_reward_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    expected_return_pct: Mapped[float] = mapped_column(Float, default=0.0)
    reasons: Mapped[dict] = mapped_column(JSON, default=dict)
