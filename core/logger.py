"""Logging configuration for code review agents."""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Structured logger with JSON output support."""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        self.logger.handlers = []

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)

        # Use JSON formatter
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def _add_context(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add contextual information to log entry."""
        context = {
            "timestamp": datetime.utcnow().isoformat(),
        }
        if extra:
            context.update(extra)
        return context

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=self._add_context(kwargs))

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=self._add_context(kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=self._add_context(kwargs))

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=self._add_context(kwargs))

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=self._add_context(kwargs))

    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra=self._add_context(kwargs))


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, level: Optional[str] = None) -> StructuredLogger:
    """Get or create a logger instance."""
    if name not in _loggers:
        from .config import get_settings
        if level is None:
            level = get_settings().log_level
        _loggers[name] = StructuredLogger(name, level)
    return _loggers[name]
