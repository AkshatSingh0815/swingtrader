"""Detected candlestick and chart patterns."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    pattern_name: Mapped[str] = mapped_column(String(64))
    pattern_type: Mapped[str] = mapped_column(String(16))  # "candlestick" | "chart"
    direction: Mapped[str] = mapped_column(String(8))       # "bullish" | "bearish" | "neutral"
    confidence: Mapped[float] = mapped_column(default=0.5)
