"""
Logging Configuration for Reconciliation System
Provides structured logging for all reconciliation operations.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "reconciliation", log_dir: str = None) -> logging.Logger:
    """
    Configure and return a logger instance with file and console handlers.

    Args:
        name: Logger name (default: 'reconciliation')
        log_dir: Directory for log files (default: project logs/ directory)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Determine log directory
    if log_dir is None:
        project_root = Path(__file__).parent.parent
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)

    # Create logs directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # File handler for all logs
    log_file = log_dir / f"reconciliation_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "reconciliation") -> logging.Logger:
    """Get an existing logger or create one if it doesn't exist."""
    return logging.getLogger(name)
