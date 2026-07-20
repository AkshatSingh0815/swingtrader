"""Loguru-based logger shared across the whole project."""
import sys
from pathlib import Path

from loguru import logger

from utils.config import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger.remove()
logger.add(sys.stdout, level=settings.LOG_LEVEL, colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
                   "<cyan>{module}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>")
logger.add(LOG_DIR / "scan_{time:YYYY-MM-DD}.log", level="DEBUG", rotation="1 day",
            retention="30 days", encoding="utf-8")

__all__ = ["logger"]
