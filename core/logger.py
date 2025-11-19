"""Logging configuration for code review agents."""

import logging
import os
import sys
from typing import Dict, Optional


class StructuredLogger:
    """Simple structured logger."""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Only add handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(self._format_message(message, kwargs))

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(self._format_message(message, kwargs))

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(self._format_message(message, kwargs))

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(self._format_message(message, kwargs))

    def _format_message(self, message: str, kwargs: dict) -> str:
        """Format message with additional context."""
        if kwargs:
            context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} | {context}"
        return message


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: Optional[str] = None) -> StructuredLogger:
    """
    Get or create a logger instance.

    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to LOG_LEVEL env var or INFO.

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        if level is None:
            level = os.getenv('LOG_LEVEL', 'INFO')
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]
