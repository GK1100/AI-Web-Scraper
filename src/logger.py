"""
Logging setup for the scraper
"""

import logging
import os
from datetime import datetime
from config import LOG_LEVEL, LOG_FILE, LOG_FORMAT


def setup_logger(name: str) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler - detailed logs
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Console handler - important logs only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def log_step(logger: logging.Logger, step: str, status: str, details: dict = None):
    """
    Log a step in the scraping process
    
    Args:
        logger: Logger instance
        step: Step name (e.g., "Intent Understanding")
        status: Status (SUCCESS, FAILED, STARTED)
        details: Additional details to log
    """
    message = f"[{step}] {status}"
    if details:
        message += f" - {details}"
    
    if status == "FAILED":
        logger.error(message)
    elif status == "SUCCESS":
        logger.info(message)
    else:
        logger.debug(message)
