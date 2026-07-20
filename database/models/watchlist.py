"""User watchlist entries."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    added_date: Mapped[dt.date] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(Text, default="")
