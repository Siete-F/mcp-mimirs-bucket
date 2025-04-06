"""
Logging utilities for Mimir's Bucket.

This module contains common logging-related utilities that can be used across
the application to ensure consistent logging behavior.
"""

import logging
import sys
from typing import Optional, TextIO, List

# Default log format used throughout the application
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Log level mapping from string representation to logging constants
LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

def get_log_level(level_str: str) -> int:
    """
    Convert a string log level to the corresponding logging constant.
    
    Args:
        level_str: String representation of log level (DEBUG, INFO, etc.)
        
    Returns:
        The corresponding logging level constant
    """
    return LOG_LEVEL_MAP.get(level_str.upper(), logging.INFO)

def create_stderr_handler(
    level: int = logging.INFO,
    formatter: Optional[logging.Formatter] = None
) -> logging.Handler:
    """
    Create a stderr handler with the given level and formatter.
    
    Args:
        level: Logging level
        formatter: Optional custom formatter. If None, uses DEFAULT_LOG_FORMAT
        
    Returns:
        Configured stderr handler
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    if formatter is None:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    
    handler.setFormatter(formatter)
    return handler

def configure_library_logger(
    logger_name: str,
    level: int = logging.INFO,
    stream: TextIO = sys.stderr,
    format_string: str = DEFAULT_LOG_FORMAT
) -> None:
    """
    Configure a third-party library's logger to use stderr.
    
    Args:
        logger_name: Name of the logger to configure
        level: Logging level to set
        stream: Stream to use (default: sys.stderr)
        format_string: Format string for the log messages
    """
    library_logger = logging.getLogger(logger_name)
    
    # Clear existing handlers to avoid duplicates
    if library_logger.hasHandlers():
        library_logger.handlers.clear()
    
    # Create and add stderr handler
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter(format_string))
    library_logger.addHandler(handler)
    library_logger.setLevel(level)
    
    # Also configure sub-loggers (in case they're used)
    for logger_name in logging.root.manager.loggerDict:
        if logger_name.startswith(logger_name + '.'):
            sub_logger = logging.getLogger(logger_name)
            if sub_logger.hasHandlers():
                sub_logger.handlers.clear()
            sub_logger.addHandler(handler)
            sub_logger.setLevel(level)

def configure_third_party_loggers(
    logger_names: List[str], 
    level: int = logging.INFO,
    stream: TextIO = sys.stderr,
    format_string: str = DEFAULT_LOG_FORMAT
) -> None:
    """
    Configure multiple third-party library loggers to use stderr.
    
    Args:
        logger_names: List of logger names to configure
        level: Logging level to set
        stream: Stream to use (default: sys.stderr)
        format_string: Format string for the log messages
    """
    for logger_name in logger_names:
        configure_library_logger(
            logger_name, 
            level=level, 
            stream=stream, 
            format_string=format_string
        )

def setup_logging(
    level: str = "INFO",
    name: str = "mimirs_bucket"
) -> logging.Logger:
    """
    Set up logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to log to
        name: Logger name

    Returns:
        Configured logger
    """
    # Map string level to logging level
    log_level = get_log_level(level)

    # Configure root logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add stderr handler
    logger.addHandler(create_stderr_handler(log_level))

    return logger
