"""News headlines with sentiment scores, and ML move-probability predictions."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    headline: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="")
    sentiment: Mapped[str] = mapped_column(String(16), default="neutral")  # positive/neutral/negative
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)     # -1..1


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)
    horizon_days: Mapped[int] = mapped_column(Integer)     # 5, 10, 20
    threshold_pct: Mapped[float] = mapped_column(Float)    # 5, 10, 15, 20
    probability: Mapped[float] = mapped_column(Float)      # 0..1
