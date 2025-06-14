"""Structured logging configuration for the YouTube Playlist Analyzer.

This module provides centralized logging configuration with JSON structured output,
proper log levels, and request tracing capabilities for production environments.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Flask, g, request


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON.

        Args:
            record: The log record to format

        Returns:
            JSON formatted string
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request context if available (in Flask request context)
        try:
            if request:
                log_entry.update(
                    {
                        "request_id": getattr(g, "request_id", None),
                        "method": request.method,
                        "url": request.url,
                        "remote_addr": request.remote_addr,
                        "user_agent": request.headers.get("User-Agent"),
                    }
                )
        except RuntimeError:
            # Outside request context
            pass

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from log record
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            ):
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def setup_logging(app: Flask, log_level: str = "INFO") -> None:
    """Configure application logging with structured JSON output.

    Args:
        app: Flask application instance
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remove default Flask handlers
    app.logger.handlers.clear()

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())

    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    console_handler.setLevel(numeric_level)
    root_logger.setLevel(numeric_level)

    # Add handler to root logger
    root_logger.addHandler(console_handler)

    # Configure Flask app logger
    app.logger.setLevel(numeric_level)
    app.logger.addHandler(console_handler)

    # Configure third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("googleapiclient").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_api_call(
    service: str,
    operation: str,
    playlist_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log API call with structured data.

    Args:
        service: Name of the service (e.g., 'youtube_api')
        operation: Operation being performed (e.g., 'get_playlist_items')
        playlist_id: YouTube playlist ID if applicable
        duration_ms: Call duration in milliseconds
        error: Error message if call failed
        **kwargs: Additional structured data to log
    """
    logger = get_logger(__name__)

    log_data = {
        "event_type": "api_call",
        "service": service,
        "operation": operation,
        "playlist_id": playlist_id,
        "duration_ms": duration_ms,
        "success": error is None,
        **kwargs,
    }

    if error:
        log_data["error"] = error
        logger.error("API call failed", extra=log_data)
    else:
        logger.info("API call completed", extra=log_data)


def log_business_event(
    event_type: str,
    playlist_id: Optional[str] = None,
    video_count: Optional[int] = None,
    analysis_type: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Log business events with structured data.

    Args:
        event_type: Type of business event (e.g., 'playlist_analyzed')
        playlist_id: YouTube playlist ID if applicable
        video_count: Number of videos processed
        analysis_type: Type of analysis performed
        **kwargs: Additional structured data to log
    """
    logger = get_logger(__name__)

    log_data = {
        "event_type": event_type,
        "playlist_id": playlist_id,
        "video_count": video_count,
        "analysis_type": analysis_type,
        **kwargs,
    }

    logger.info("Business event", extra=log_data)
