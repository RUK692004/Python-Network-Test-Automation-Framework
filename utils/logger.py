"""
Centralized logging utility for the Network Test Automation Framework.

Provides a configured logger with console (stdout) and file handlers.
Logs are saved in the 'logs/network_tests.log' file.
"""

import logging
from pathlib import Path
from typing import Optional

DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "network_tests.log"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str = "network_framework",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up and return a configured logger instance.

    Args:
        name: Name of the logger module.
        log_file: Optional custom path for the log file.
        level: Logging severity level (default: logging.INFO).

    Returns:
        logging.Logger: Configured logger with console and file handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    target_log_file = log_file or DEFAULT_LOG_FILE
    log_dir = target_log_file.parent

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as err:
        logger.warning(f"Could not create log file handler at {target_log_file}: {err}")

    return logger


def get_logger(name: str = "network_framework") -> logging.Logger:
    """
    Retrieve an existing logger or create a default configured logger.

    Args:
        name: Logger module name.

    Returns:
        logging.Logger instance.
    """
    return setup_logger(name)
