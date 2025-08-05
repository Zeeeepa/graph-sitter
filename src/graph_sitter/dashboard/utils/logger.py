"""Logging utilities for the dashboard."""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
        
    # Set log level
    log_level = level or "INFO"
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger


def configure_dashboard_logging(level: str = "INFO") -> None:
    """Configure logging for the entire dashboard.
    
    Args:
        level: Log level for all dashboard loggers
    """
    # Configure root dashboard logger
    dashboard_logger = get_logger("graph_sitter.dashboard", level)
    
    # Configure service loggers
    get_logger("graph_sitter.dashboard.services", level)
    get_logger("graph_sitter.dashboard.api", level)
    get_logger("graph_sitter.dashboard.utils", level)
    
    dashboard_logger.info(f"Dashboard logging configured at {level} level")

