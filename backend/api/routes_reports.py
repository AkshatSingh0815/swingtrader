"""Generates daily/weekly PDF and Excel reports from the latest scan data."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import desc
from sqlalchemy.orm import Session

from database.db import get_db
from database.models.score import Score
from database.models.signal import Signal

router = APIRouter()
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)


@router.get("/reports/daily.pdf")
def daily_pdf(db: Session = Depends(get_db)):
    latest_date = db.query(Score.date).order_by(desc(Score.date)).first()
    scores = (db.query(Score).filter(Score.date == latest_date[0]).order_by(Score.rank).limit(25).all()
              if latest_date else [])

    path = REPORTS_DIR / f"daily_report_{dt.date.today()}.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Daily Swing Trading Report — {dt.date.today()}", styles["Title"]), Spacer(1, 12)]

    data = [["Rank", "Symbol", "Overall", "Technical", "Momentum", "Volume", "Category"]]
    for s in scores:
        data.append([s.rank, s.symbol, s.overall_score, s.technical_score,
                     s.momentum_score, s.volume_score, s.category])
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    doc.build(elements)
    return FileResponse(path, filename=path.name, media_type="application/pdf")


@router.get("/reports/weekly.xlsx")
def weekly_excel(db: Session = Depends(get_db)):
    week_ago = dt.date.today() - dt.timedelta(days=7)
    signals = db.query(Signal).filter(Signal.date >= week_ago).order_by(desc(Signal.date)).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Weekly Signals"
    ws.append(["Date", "Symbol", "Signal", "Entry", "Stop Loss", "Target 1", "Target 2",
               "Target 3", "Risk:Reward", "Expected Return %"])
    for s in signals:
        ws.append([str(s.date), s.symbol, s.signal_type, s.entry, s.stop_loss, s.target_1,
                   s.target_2, s.target_3, s.risk_reward_ratio, s.expected_return_pct])

    path = REPORTS_DIR / f"weekly_report_{dt.date.today()}.xlsx"
    wb.save(path)
    return FileResponse(path, filename=path.name,
                         media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
