"""
Logging utilities for DocMind-AI.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_config


def setup_logger(
    name: str = "docmind",
    log_file: Optional[str] = None,
    log_level: Optional[str] = None,
    detailed: Optional[bool] = None,
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.

    Args:
        name: Logger name
        log_file: Log file path (uses config if not provided)
        log_level: Log level (uses config if not provided)
        detailed: Whether to use detailed logging (uses config if not provided)

    Returns:
        Configured logger instance
    """
    config = get_config()

    # Use config values if not provided
    if log_file is None:
        log_file = config.log_file
    if log_level is None:
        log_level = config.log_level
    if detailed is None:
        detailed = config.enable_detailed_logging

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers = []

    # Create formatters
    if detailed:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Global logger instance
_global_logger: Optional[logging.Logger] = None


def get_logger(name: str = "docmind") -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    global _global_logger

    if _global_logger is None:
        _global_logger = setup_logger(name)

    return _global_logger


def log_agent_step(
    agent_name: str,
    action: str,
    details: Optional[dict] = None,
    level: str = "info",
):
    """
    Log an agent step with structured information.

    Args:
        agent_name: Name of the agent
        action: Action being performed
        details: Additional details to log
        level: Log level (info, debug, warning, error)
    """
    logger = get_logger()
    log_func = getattr(logger, level.lower())

    message = f"[{agent_name}] {action}"
    if details:
        detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
        message += f" | {detail_str}"

    log_func(message)


def log_cost(
    operation: str,
    cost: float,
    details: Optional[dict] = None,
):
    """
    Log cost information.

    Args:
        operation: Operation name
        cost: Cost in USD
        details: Additional details
    """
    logger = get_logger()
    message = f"💰 Cost: ${cost:.4f} for {operation}"

    if details:
        detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
        message += f" | {detail_str}"

    logger.info(message)


def log_performance(
    operation: str,
    duration: float,
    details: Optional[dict] = None,
):
    """
    Log performance information.

    Args:
        operation: Operation name
        duration: Duration in seconds
        details: Additional details
    """
    logger = get_logger()
    message = f"⏱️  Performance: {duration:.2f}s for {operation}"

    if details:
        detail_str = ", ".join([f"{k}={v}" for k, v in details.items()])
        message += f" | {detail_str}"

    logger.info(message)
