"""The nightly orchestrator. Run directly (`python -m scanner.scan_runner`)
or scheduled via GitHub Actions / APScheduler / cron.

Pipeline: symbol universe -> price data -> per-stock strategy evaluation ->
persist scores/signals/patterns/news/ML -> rank -> send alerts.
"""
from __future__ import annotations

import datetime as dt

from database.db import get_session, init_db
from database.models.indicator import Indicator
from database.models.news import MLPrediction, NewsSentiment
from database.models.pattern import Pattern
from database.models.score import Score
from database.models.signal import Signal
from database.models.stock import Stock
from scanner.categorize import categorize
from services.alerts import send_alert
from services.data_fetcher import fetch_universe
from services.nse_symbols import get_symbol_universe
from strategies.swing_strategy import evaluate_stock
from utils.config import settings
from utils.logger import logger


def run_scan(universe: str | None = None, fetch_news: bool = True) -> list[dict]:
    universe = universe or settings.SCAN_UNIVERSE
    today = dt.date.today()
    logger.info(f"=== Starting scan for {today} | universe={universe} ===")

    symbols = get_symbol_universe(universe)
    price_data = fetch_universe(symbols)

    results = []
    with get_session() as db:
        sector_lookup = {s.symbol: s.sector for s in db.query(Stock).all()}

    for symbol, df in price_data.items():
        try:
            result = evaluate_stock(symbol, name=symbol, price_df=df, fetch_news_flag=fetch_news)
        except Exception as e:
            logger.warning(f"[{symbol}] evaluation failed: {e}")
            continue
        if not result:
            continue

        cats = categorize(symbol, sector_lookup.get(symbol, ""), result["snapshot"],
                           result["patterns"], result["scores"])
        result["categories"] = cats
        results.append(result)

    results.sort(key=lambda r: r["scores"]["overall_score"], reverse=True)
    for rank, r in enumerate(results, start=1):
        r["rank"] = rank

    _persist_results(results, today)
    _send_alerts(results)

    logger.info(f"=== Scan complete: {len(results)} stocks evaluated, top score "
                f"{results[0]['scores']['overall_score'] if results else 'n/a'} ===")
    return results


def _persist_results(results: list[dict], scan_date: dt.date) -> None:
    with get_session() as db:
        for r in results:
            symbol, snap = r["symbol"], r["snapshot"]

            db.merge(Indicator(symbol=symbol, date=scan_date, **{
                k: v for k, v in snap.items() if k in Indicator.__table__.columns.keys() and k not in ("id",)
            }))

            for p in r["patterns"]:
                db.add(Pattern(symbol=symbol, date=scan_date, pattern_name=p["name"],
                                pattern_type="chart" if "confidence" in p else "candlestick",
                                direction=p["direction"], confidence=p.get("confidence", 0.5)))

            if r["sentiment"]:
                db.add(NewsSentiment(symbol=symbol, date=scan_date, headline="(aggregated)",
                                      sentiment=r["sentiment"]["label"], sentiment_score=r["sentiment"]["score"]))

            for pred in r["ml_predictions"]:
                db.add(MLPrediction(symbol=symbol, date=scan_date, horizon_days=pred["horizon_days"],
                                     threshold_pct=pred["threshold_pct"], probability=pred["probability"]))

            db.merge(Score(symbol=symbol, date=scan_date, rank=r["rank"],
                            category=",".join(r["categories"]), **r["scores"]))

            plan = r["risk_plan"]
            db.add(Signal(symbol=symbol, date=scan_date, signal_type=r["signal"]["signal_type"],
                           entry=plan.entry, stop_loss=plan.stop_loss, target_1=plan.target_1,
                           target_2=plan.target_2, target_3=plan.target_3, position_size=plan.position_size,
                           risk_pct=plan.risk_pct, capital_allocated=plan.capital_allocated,
                           risk_reward_ratio=plan.risk_reward_ratio,
                           expected_return_pct=plan.expected_return_pct, reasons=r["signal"]["reasons"]))


def _send_alerts(results: list[dict]) -> None:
    strong_buys = [r for r in results if r["signal"]["signal_type"] == "STRONG_BUY"]
    if not strong_buys:
        return
    lines = [f"{r['symbol']}: score {r['scores']['overall_score']:.1f}, "
             f"entry {r['risk_plan'].entry}, target1 {r['risk_plan'].target_1}"
             for r in strong_buys[:15]]
    message = "🚀 STRONG BUY signals today:\n" + "\n".join(lines)
    send_alert(message)


if __name__ == "__main__":
    init_db()
    run_scan()
