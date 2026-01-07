"""
Centralized logging configuration for Dividend Recovery System.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

from config import LOGS_DIR


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON.
    Useful for log aggregation and analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'stock_ticker'):
            log_data['stock_ticker'] = record.stock_ticker
        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation
        if hasattr(record, 'duration_ms'):
            log_data['duration_ms'] = record.duration_ms

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format: [TIMESTAMP] LEVEL - module.function:line - message
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"{color}[{timestamp}] {record.levelname}{reset} - {record.module}.{record.funcName}:{record.lineno} - {record.getMessage()}"

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging(
    name: str = "dividend_recovery",
    level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    json_format: bool = False
) -> logging.Logger:
    """
    Setup logging with file and console handlers.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        json_format: Use JSON format for file logs

    Returns:
        Configured logger

    Example:
        >>> logger = setup_logging("my_module", level="DEBUG")
        >>> logger.info("Processing started", extra={'stock_ticker': 'ENEL.MI'})
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))
    logger.propagate = False

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        # Create log file with date
        log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        if json_format:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
                )
            )

        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default configuration.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting process")
    """
    from config import get_config

    # Check if logger already exists
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    # Create new logger with config settings
    cfg = get_config()
    return setup_logging(
        name=name,
        level=cfg.data_collection.log_level,
        log_to_file=cfg.data_collection.log_to_file,
        log_to_console=True,
        json_format=False
    )


class OperationLogger:
    """
    Context manager for logging operations with timing.

    Example:
        >>> logger = get_logger(__name__)
        >>> with OperationLogger(logger, "download_stock_data", stock_ticker="ENEL.MI"):
        >>>     # ... do work ...
        >>>     pass
        >>> # Automatically logs duration and success/failure
    """

    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.extra = kwargs
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}", extra=self.extra)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000

        extra = {**self.extra, 'duration_ms': duration_ms, 'operation': self.operation}

        if exc_type is None:
            self.logger.info(f"Completed: {self.operation} ({duration_ms:.0f}ms)", extra=extra)
        else:
            self.logger.error(
                f"Failed: {self.operation} ({duration_ms:.0f}ms) - {exc_type.__name__}: {exc_val}",
                extra=extra,
                exc_info=True
            )

        # Don't suppress exceptions
        return False


# Create default logger
default_logger = get_logger("dividend_recovery")


if __name__ == "__main__":
    # Test logging
    logger = setup_logging("test", level="DEBUG", json_format=False)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    # Test with extra fields
    logger.info("Processing stock", extra={'stock_ticker': 'ENEL.MI', 'operation': 'download'})

    # Test operation logger
    with OperationLogger(logger, "test_operation", stock_ticker="TEST.MI"):
        import time
        time.sleep(0.1)

    # Test with exception
    try:
        with OperationLogger(logger, "failing_operation"):
            raise ValueError("Test error")
    except ValueError:
        pass

    print(f"\nLogs written to: {LOGS_DIR}")
