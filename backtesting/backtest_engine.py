"""Simple event-driven backtester for the swing strategy: replays historical
BUY signals day-by-day, applies the risk plan (stop-loss/targets), and
computes standard performance metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd

from scanner.indicators import compute_all_indicators, latest_snapshot
from scanner.candlestick_patterns import detect_all as detect_candlesticks
from scanner.chart_patterns import detect_chart_patterns
from scanner.scoring import composite_score
from signals.risk_management import build_risk_plan
from signals.signal_engine import generate_signal


def backtest_symbol(price_df: pd.DataFrame, max_hold_days: int = 20) -> list[dict]:
    """Walk forward through history, generating a signal each day using only
    data up to that day (no lookahead), and simulate the trade outcome if a
    BUY/STRONG_BUY fires."""
    trades = []
    ind_df = compute_all_indicators(price_df)
    if ind_df.empty or len(ind_df) < 210:
        return trades

    i = 210  # need enough history for EMA200 etc.
    while i < len(ind_df) - 1:
        window = ind_df.iloc[: i + 1]
        snapshot = latest_snapshot(window)
        candlesticks = detect_candlesticks(window.tail(5))
        chart_patterns = detect_chart_patterns(window)
        scores = composite_score(snapshot)
        plan = build_risk_plan(snapshot.get("close", 0.0), snapshot.get("atr_14"))
        signal = generate_signal(snapshot, candlesticks + chart_patterns, None, scores["overall_score"])

        if signal["signal_type"] in ("BUY", "STRONG_BUY"):
            outcome = _simulate_trade(ind_df, entry_idx=i, plan=plan, max_hold_days=max_hold_days)
            trades.append(outcome)
            i += outcome["days_held"]  # skip ahead past this trade
        else:
            i += 1

    return trades


def _simulate_trade(ind_df: pd.DataFrame, entry_idx: int, plan, max_hold_days: int) -> dict:
    future = ind_df.iloc[entry_idx + 1: entry_idx + 1 + max_hold_days]
    for day_offset, (_, row) in enumerate(future.iterrows(), start=1):
        if row["low"] <= plan.stop_loss:
            return {"result": "stop_loss", "return_pct": (plan.stop_loss - plan.entry) / plan.entry * 100,
                    "days_held": day_offset}
        if row["high"] >= plan.target_1:
            return {"result": "target_hit", "return_pct": (plan.target_1 - plan.entry) / plan.entry * 100,
                    "days_held": day_offset}
    # time-based exit at last available close
    if len(future):
        exit_price = future["close"].iloc[-1]
        return {"result": "time_exit", "return_pct": (exit_price - plan.entry) / plan.entry * 100,
                "days_held": len(future)}
    return {"result": "no_data", "return_pct": 0.0, "days_held": 1}


def compute_metrics(all_trades: list[dict], risk_free_rate: float = 0.06) -> dict:
    """Standard swing-strategy performance metrics from a list of trade results."""
    if not all_trades:
        return {"total_trades": 0, "win_rate": 0.0, "avg_profit_pct": 0.0, "avg_loss_pct": 0.0,
                "sharpe_ratio": 0.0, "max_drawdown_pct": 0.0, "annual_return_pct": 0.0}

    returns = np.array([t["return_pct"] for t in all_trades])
    wins = returns[returns > 0]
    losses = returns[returns <= 0]

    win_rate = len(wins) / len(returns) * 100
    avg_profit = wins.mean() if len(wins) else 0.0
    avg_loss = losses.mean() if len(losses) else 0.0

    daily_equivalent = returns / 100  # treat each trade's return independently
    sharpe = (daily_equivalent.mean() / daily_equivalent.std() * np.sqrt(252)
              if daily_equivalent.std() > 0 else 0.0)

    equity_curve = (1 + daily_equivalent).cumprod()
    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max
    max_dd = drawdown.min() * 100 if len(drawdown) else 0.0

    total_return = equity_curve[-1] - 1 if len(equity_curve) else 0.0
    avg_days_held = np.mean([t["days_held"] for t in all_trades])
    trades_per_year = 252 / avg_days_held if avg_days_held else 0
    annual_return = ((1 + total_return) ** (trades_per_year / max(len(all_trades), 1)) - 1) * 100 \
        if total_return > -1 else -100.0

    return {
        "total_trades": len(all_trades),
        "win_rate": round(win_rate, 2),
        "avg_profit_pct": round(float(avg_profit), 2),
        "avg_loss_pct": round(float(avg_loss), 2),
        "sharpe_ratio": round(float(sharpe), 2),
        "max_drawdown_pct": round(float(max_dd), 2),
        "annual_return_pct": round(float(annual_return), 2),
    }
