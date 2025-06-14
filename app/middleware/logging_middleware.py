"""Logging Middleware.

This module provides middleware for logging requests and responses.
"""

import logging
import time

from flask import Flask, g, request


class LoggingMiddleware:
    """Middleware for logging requests and responses.

    This class implements middleware for logging requests and responses.
    It logs information about incoming requests and outgoing responses,
    including request method, path, status code, and response time.

    Attributes:
        app: The Flask application.
        logger: The logger to use.
    """

    def __init__(self, app: Flask, logger=None):
        """Initialize the LoggingMiddleware.

        Args:
            app: The Flask application.
            logger: The logger to use. If None, a new logger is created.
        """
        self.app = app
        self.logger = logger or logging.getLogger(__name__)
        self._setup_middleware()

    def _setup_middleware(self):
        """Set up the middleware.

        This method sets up the middleware by registering before_request
        and after_request handlers with the Flask application.
        """
        self.app.before_request(self._before_request)
        self.app.after_request(self._after_request)

    def _before_request(self):
        """Handle before_request event.

        This method is called before each request. It logs information
        about the incoming request and stores the request start time.
        """
        g.start_time = time.time()
        try:
            self.logger.info(
                f"Request: {request.method} {request.path} (IP: {request.remote_addr})"
            )
        except Exception as e:
            # Log the exception but don't disrupt the request flow
            print(f"Logging error in before_request: {e}")

    def _after_request(self, response):
        """Handle after_request event.

        This method is called after each request. It logs information
        about the outgoing response, including status code and response time.

        Args:
            response: The response object.

        Returns:
            The response object.
        """
        if hasattr(g, "start_time"):
            try:
                elapsed_time = time.time() - g.start_time
                self.logger.info(
                    f"Response: {request.method} {request.path} "
                    f"(Status: {response.status_code}, Time: {elapsed_time:.4f}s)"
                )
            except Exception as e:
                # Log the exception but don't disrupt the response flow
                self.logger.error(f"Logging error in after_request: {e}")
        return response


def setup_logging_middleware(app: Flask) -> LoggingMiddleware:
    """Set up logging middleware.

    This function sets up logging middleware for the application.

    Args:
        app: The Flask application.

    Returns:
        The LoggingMiddleware instance.
    """
    logger = logging.getLogger(__name__)
    return LoggingMiddleware(app, logger)
