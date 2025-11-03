"""
Logging configuration
"""
from loguru import logger
import sys
from backend.config import settings

# Remove default logger
logger.remove()

# Add console logger with color
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
    colorize=True
)

# Add file logger
logger.add(
    "data/logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
)

