"""Streamlit dashboard. Run: streamlit run frontend/app.py

Reads directly from the SQLite DB (fast, no network hop needed for a local
personal tool) rather than going through the FastAPI layer — FastAPI is
still there for programmatic/external access, but the dashboard doesn't
need to round-trip through HTTP for its own DB.
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import desc

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.db import get_session, init_db  # noqa: E402
from database.models.indicator import Indicator  # noqa: E402
from database.models.pattern import Pattern  # noqa: E402
from database.models.portfolio import PortfolioHolding  # noqa: E402
from database.models.score import Score  # noqa: E402
from database.models.signal import Signal  # noqa: E402
from database.models.stock import PriceHistory  # noqa: E402
from database.models.watchlist import WatchlistItem  # noqa: E402

st.set_page_config(page_title="NSE Swing Trader", layout="wide", page_icon="📈")

init_db()

# ---------------- Sidebar: dark mode + nav ----------------
st.sidebar.title("📈 NSE Swing Trader")
dark_mode = st.sidebar.toggle("Dark mode", value=True)
page = st.sidebar.radio("Navigate", [
    "Dashboard", "Market Heatmap", "Stock Detail", "Watchlist", "Portfolio", "AI Assistant",
])

if dark_mode:
    st.markdown("""
        <style>
        .stApp { background-color: #0e1117; color: #e6e6e6; }
        </style>
    """, unsafe_allow_html=True)


def latest_scan_date(db) -> dt.date | None:
    row = db.query(Score.date).order_by(desc(Score.date)).first()
    return row[0] if row else None


def scores_df(db, category: str | None = None, limit: int = 20) -> pd.DataFrame:
    d = latest_scan_date(db)
    if not d:
        return pd.DataFrame()
    q = db.query(Score).filter(Score.date == d)
    if category:
        q = q.filter(Score.category.contains(category))
    rows = q.order_by(Score.rank).limit(limit).all()
    return pd.DataFrame([{
        "Rank": r.rank, "Symbol": r.symbol, "Overall": r.overall_score,
        "Technical": r.technical_score, "Momentum": r.momentum_score,
        "Volume": r.volume_score, "News": r.news_score, "Category": r.category,
    } for r in rows])


# ==================== DASHBOARD ====================
if page == "Dashboard":
    st.title("Daily Market Scan")
    with get_session() as db:
        d = latest_scan_date(db)
        if not d:
            st.warning("No scan data yet. Run `python -m scanner.scan_runner` first "
                       "(or wait for the nightly GitHub Action).")
        else:
            st.caption(f"Latest scan: {d}")
            tabs = st.tabs([
                "🏆 Top Swing Trades", "🚀 Breakouts", "⚡ Momentum", "🪙 Penny Stocks",
                "💰 Dividend", "🚆 Railway", "🏦 Banking", "🛡️ Defence", "🌱 Renewable",
            ])
            categories = ["swing", "breakout", "momentum", "penny", "dividend",
                          "railway", "banking", "defence", "renewable"]
            for tab, cat in zip(tabs, categories):
                with tab:
                    df = scores_df(db, category=cat)
                    if df.empty:
                        st.info("No stocks in this category today.")
                    else:
                        st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("Today's Signals")
            signals = db.query(Signal).filter(Signal.date == d).order_by(desc(Signal.expected_return_pct)).limit(30).all()
            if signals:
                sig_df = pd.DataFrame([{
                    "Symbol": s.symbol, "Signal": s.signal_type, "Entry": s.entry,
                    "Stop Loss": s.stop_loss, "Target 1": s.target_1, "Target 2": s.target_2,
                    "Target 3": s.target_3, "R:R": s.risk_reward_ratio,
                    "Expected Return %": s.expected_return_pct,
                } for s in signals])
                st.dataframe(sig_df, use_container_width=True, hide_index=True)

# ==================== MARKET HEATMAP ====================
elif page == "Market Heatmap":
    st.title("Market Heatmap")
    with get_session() as db:
        d = latest_scan_date(db)
        if not d:
            st.warning("No scan data yet.")
        else:
            rows = db.query(Score).filter(Score.date == d).all()
            df = pd.DataFrame([{"Symbol": r.symbol, "Score": r.overall_score, "Category": r.category} for r in rows])
            if not df.empty:
                fig = go.Figure(go.Treemap(
                    labels=df["Symbol"], parents=[""] * len(df), values=df["Score"].clip(lower=1),
                    marker=dict(colors=df["Score"], colorscale="RdYlGn", cmid=50),
                    text=df["Score"].round(1), textinfo="label+text",
                ))
                fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=600)
                st.plotly_chart(fig, use_container_width=True)

# ==================== STOCK DETAIL ====================
elif page == "Stock Detail":
    st.title("Stock Detail & Chart")
    symbol = st.text_input("Enter NSE symbol (e.g. RELIANCE)", "RELIANCE").upper()
    with get_session() as db:
        prices = (db.query(PriceHistory).filter_by(symbol=symbol).order_by(PriceHistory.date).all())
        if not prices:
            st.warning(f"No cached price history for {symbol} yet. It will appear after the next scan.")
        else:
            df = pd.DataFrame([{"date": p.date, "open": p.open, "high": p.high,
                                 "low": p.low, "close": p.close, "volume": p.volume} for p in prices])
            fig = go.Figure(data=[go.Candlestick(
                x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                name=symbol,
            )])
            fig.update_layout(height=500, xaxis_rangeslider_visible=False,
                               margin=dict(t=20, l=10, r=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

            latest_ind = db.query(Indicator).filter_by(symbol=symbol).order_by(desc(Indicator.date)).first()
            latest_score = db.query(Score).filter_by(symbol=symbol).order_by(desc(Score.date)).first()
            patterns = db.query(Pattern).filter_by(symbol=symbol).order_by(desc(Pattern.date)).limit(5).all()

            cols = st.columns(4)
            if latest_ind:
                cols[0].metric("RSI (14)", f"{latest_ind.rsi_14:.1f}" if latest_ind.rsi_14 else "n/a")
                cols[1].metric("ADX (14)", f"{latest_ind.adx_14:.1f}" if latest_ind.adx_14 else "n/a")
                cols[2].metric("ATR (14)", f"{latest_ind.atr_14:.2f}" if latest_ind.atr_14 else "n/a")
            if latest_score:
                cols[3].metric("Overall Score", f"{latest_score.overall_score:.1f}/100")

            if patterns:
                st.subheader("Recent Patterns")
                st.write(", ".join(f"{p.pattern_name} ({p.direction})" for p in patterns))

# ==================== WATCHLIST ====================
elif page == "Watchlist":
    st.title("Watchlist")
    with get_session() as db:
        new_symbol = st.text_input("Add symbol to watchlist").upper()
        if st.button("Add") and new_symbol:
            if not db.query(WatchlistItem).filter_by(symbol=new_symbol).first():
                db.add(WatchlistItem(symbol=new_symbol, added_date=dt.date.today()))
                st.success(f"Added {new_symbol}")
            else:
                st.info(f"{new_symbol} already on watchlist")

        items = db.query(WatchlistItem).all()
        for item in items:
            c1, c2, c3 = st.columns([2, 4, 1])
            c1.write(f"**{item.symbol}**")
            c2.write(item.notes or "—")
            if c3.button("Remove", key=f"rm_{item.id}"):
                db.delete(item)
                st.rerun()

# ==================== PORTFOLIO ====================
elif page == "Portfolio":
    st.title("Portfolio Tracker")
    with get_session() as db:
        holdings = db.query(PortfolioHolding).all()
        if holdings:
            df = pd.DataFrame([{
                "Symbol": h.symbol, "Qty": h.quantity, "Buy Price": h.buy_price,
                "Current Price": h.current_price, "Invested": h.invested,
                "Current Value": h.current_value, "PnL": h.pnl, "PnL %": round(h.pnl_pct, 2),
            } for h in holdings])
            st.dataframe(df, use_container_width=True, hide_index=True)
            total_pnl = df["PnL"].sum()
            st.metric("Total PnL", f"₹{total_pnl:,.2f}")
        else:
            st.info("No holdings yet. Add trades via the API (`POST /api/v1/portfolio`).")

# ==================== AI ASSISTANT ====================
elif page == "AI Assistant":
    st.title("AI Chat Assistant")
    st.caption("Ask things like 'Should I buy RELIANCE?' or 'Explain RSI' "
               "(answers are grounded in the latest scan data in your DB).")
    question = st.text_input("Your question")
    if question:
        import requests
        try:
            resp = requests.post("http://localhost:8000/api/v1/chat", json={"question": question}, timeout=10)
            st.write(resp.json().get("answer", "No answer."))
        except Exception:
            st.error("Could not reach the FastAPI backend. Start it with: "
                     "`uvicorn backend.main:app --reload`")
