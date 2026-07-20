"""Sends alerts via Telegram and/or email. Both are best-effort: a missing
config or network failure logs a warning instead of crashing the scan."""
from __future__ import annotations

import smtplib
from email.mime.text import MIMEText

import requests

from utils.config import settings
from utils.logger import logger


def send_telegram(message: str) -> bool:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured; skipping.")
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, data={"chat_id": settings.TELEGRAM_CHAT_ID, "text": message}, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")
        return False


def send_email(subject: str, message: str) -> bool:
    if not settings.SMTP_USER or not settings.ALERT_EMAIL_TO:
        logger.debug("Email not configured; skipping.")
        return False
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_USER
        msg["To"] = settings.ALERT_EMAIL_TO
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.warning(f"Email alert failed: {e}")
        return False


def send_alert(message: str, subject: str = "Swing Trader Alert") -> None:
    """Fire-and-forget to every configured channel."""
    send_telegram(message)
    send_email(subject, message)
