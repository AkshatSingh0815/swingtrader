"""Computes a complete risk-management plan for a candidate trade:
entry, ATR-based stop loss, three targets, position size for a given
account, risk %, and risk:reward ratio."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskPlan:
    entry: float
    stop_loss: float
    target_1: float
    target_2: float
    target_3: float
    position_size: int
    risk_pct: float
    capital_allocated: float
    risk_reward_ratio: float
    expected_return_pct: float


def build_risk_plan(
    close: float,
    atr: float | None,
    account_capital: float = 100_000.0,
    risk_per_trade_pct: float = 1.0,
    atr_stop_multiplier: float = 1.5,
    target_multiples: tuple[float, float, float] = (1.5, 2.5, 4.0),
) -> RiskPlan:
    """
    entry            = last close (swing entries are typically next-day-open,
                        but we use close as the reference price the scan runs on)
    stop_loss         = entry - atr_stop_multiplier * ATR (volatility-adjusted)
    target_1/2/3      = entry + multiple * (entry - stop_loss)
    position_size     = (account_capital * risk_per_trade_pct%) / per-share risk
    risk_reward_ratio = (target_1 - entry) / (entry - stop_loss)
    """
    atr = atr or (close * 0.02)  # fallback: assume ~2% daily volatility if ATR missing
    entry = close
    per_share_risk = max(atr * atr_stop_multiplier, 0.01)
    stop_loss = round(entry - per_share_risk, 2)

    t1 = round(entry + target_multiples[0] * per_share_risk, 2)
    t2 = round(entry + target_multiples[1] * per_share_risk, 2)
    t3 = round(entry + target_multiples[2] * per_share_risk, 2)

    risk_amount = account_capital * (risk_per_trade_pct / 100)
    position_size = int(risk_amount / per_share_risk) if per_share_risk > 0 else 0
    capital_allocated = round(position_size * entry, 2)

    rr_ratio = round((t1 - entry) / per_share_risk, 2) if per_share_risk else 0.0
    expected_return_pct = round((t1 - entry) / entry * 100, 2) if entry else 0.0

    return RiskPlan(
        entry=round(entry, 2), stop_loss=stop_loss,
        target_1=t1, target_2=t2, target_3=t3,
        position_size=position_size, risk_pct=risk_per_trade_pct,
        capital_allocated=capital_allocated, risk_reward_ratio=rr_ratio,
        expected_return_pct=expected_return_pct,
    )
