"""Daily technical indicator values, one row per symbol per date."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class Indicator(Base):
    __tablename__ = "indicators"
    __table_args__ = (UniqueConstraint("symbol", "date", name="uq_ind_symbol_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    date: Mapped[dt.date] = mapped_column(Date, index=True)

    rsi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_signal: Mapped[float | None] = mapped_column(Float, nullable=True)
    macd_hist: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema_20: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema_50: Mapped[float | None] = mapped_column(Float, nullable=True)
    ema_200: Mapped[float | None] = mapped_column(Float, nullable=True)
    sma_20: Mapped[float | None] = mapped_column(Float, nullable=True)
    sma_50: Mapped[float | None] = mapped_column(Float, nullable=True)
    vwap: Mapped[float | None] = mapped_column(Float, nullable=True)
    atr_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    adx_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    supertrend: Mapped[float | None] = mapped_column(Float, nullable=True)
    supertrend_dir: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 up, -1 down
    bb_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    bb_mid: Mapped[float | None] = mapped_column(Float, nullable=True)
    bb_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    stochrsi_k: Mapped[float | None] = mapped_column(Float, nullable=True)
    stochrsi_d: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_avg_20: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    obv: Mapped[float | None] = mapped_column(Float, nullable=True)
    mfi_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    cci_20: Mapped[float | None] = mapped_column(Float, nullable=True)
    ichimoku_conv: Mapped[float | None] = mapped_column(Float, nullable=True)
    ichimoku_base: Mapped[float | None] = mapped_column(Float, nullable=True)
    ichimoku_span_a: Mapped[float | None] = mapped_column(Float, nullable=True)
    ichimoku_span_b: Mapped[float | None] = mapped_column(Float, nullable=True)
    close: Mapped[float | None] = mapped_column(Float, nullable=True)
