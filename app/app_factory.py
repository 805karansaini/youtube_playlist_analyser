"""Application Factory.

This module provides a factory function for creating Flask applications
with proper logging, error handling, and security configuration.
"""

import time
import uuid

from core.config import Config
from core.container import Container
from core.logging_config import get_logger, setup_logging
from flask import Flask, g, jsonify, request


def create_app(config_object=None) -> Flask:
    """Create a Flask application.

    This function implements the Application Factory pattern to create
    a Flask application. It configures the application, initializes
    dependencies, sets up logging, and registers blueprints.

    Args:
        config_object: Configuration object to use.

    Returns:
        A configured Flask application.
    """
    app = Flask(__name__)

    # Load configuration
    config = Config()
    app.config.from_object(config)

    # Override with provided config if available
    if config_object:
        app.config.from_object(config_object)

    # Setup structured logging
    setup_logging(app, config.LOG_LEVEL)
    logger = get_logger(__name__)

    # Initialize container
    container = Container()
    app.container = container
    app.config_instance = config

    # Register middleware
    register_middleware(app)

    # Register blueprints
    from routes import home_routes, export_routes

    app.register_blueprint(home_routes.bp)
    app.register_blueprint(export_routes.bp)

    # Register error handlers
    register_error_handlers(app)

    # Add health check endpoint
    register_health_check(app)

    logger.info(
        "Application created successfully",
        extra={
            "environment": config.ENVIRONMENT,
            "debug": config.DEBUG,
            "log_level": config.LOG_LEVEL,
        },
    )

    return app


def register_middleware(app: Flask) -> None:
    """Register middleware for request processing.

    Args:
        app: The Flask application.
    """

    @app.before_request
    def before_request():
        """Add request ID and logging context before each request."""
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()

        logger = get_logger(__name__)
        logger.info(
            "Request started",
            extra={
                "request_id": g.request_id,
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get("User-Agent"),
            },
        )

    @app.after_request
    def after_request(response):
        """Log request completion and add response headers."""
        logger = get_logger(__name__)
        logger.info(
            "Request completed",
            extra={
                "request_id": getattr(g, "request_id", None),
                "status_code": response.status_code,
                "content_length": response.content_length,
            },
        )

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        return response


def register_error_handlers(app: Flask) -> None:
    """Register comprehensive error handlers for the application.

    Args:
        app: The Flask application.
    """
    from exceptions.exception import PlaylistAnalysisError, YouTubeApiError
    from flask import jsonify, render_template, request

    logger = get_logger(__name__)

    @app.errorhandler(YouTubeApiError)
    def handle_youtube_api_error(error):
        """Handle YouTube API errors with proper logging.

        Args:
            error: The YouTube API error to handle.

        Returns:
            Error response with appropriate format.
        """
        logger.error(
            "YouTube API error occurred",
            extra={
                "error_type": "youtube_api_error",
                "error_message": str(error),
                "request_id": getattr(g, "request_id", None),
            },
        )

        if request.is_json or request.headers.get("Accept") == "application/json":
            return (
                jsonify(
                    {
                        "error": "YouTube API Error",
                        "message": str(error),
                        "request_id": getattr(g, "request_id", None),
                    }
                ),
                400,
            )

        return (
            render_template(
                "home.html",
                display_text=[
                    "YouTube API Error",
                    str(error),
                ],
            ),
            400,
        )

    @app.errorhandler(PlaylistAnalysisError)
    def handle_playlist_analysis_error(error):
        """Handle playlist analysis errors with proper logging.

        Args:
            error: The playlist analysis error to handle.

        Returns:
            Error response with appropriate format.
        """
        logger.error(
            "Playlist analysis error occurred",
            extra={
                "error_type": "playlist_analysis_error",
                "error_message": str(error),
                "request_id": getattr(g, "request_id", None),
            },
        )

        if request.is_json or request.headers.get("Accept") == "application/json":
            return (
                jsonify(
                    {
                        "error": "Playlist Analysis Error",
                        "message": str(error),
                        "request_id": getattr(g, "request_id", None),
                    }
                ),
                400,
            )

        return (
            render_template(
                "home.html",
                display_text=[
                    "Playlist Analysis Error",
                    str(error),
                ],
            ),
            400,
        )

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle validation errors."""
        logger.warning(
            "Validation error occurred",
            extra={
                "error_type": "validation_error",
                "error_message": str(error),
                "request_id": getattr(g, "request_id", None),
            },
        )

        if request.is_json or request.headers.get("Accept") == "application/json":
            return (
                jsonify(
                    {
                        "error": "Validation Error",
                        "message": str(error),
                        "request_id": getattr(g, "request_id", None),
                    }
                ),
                400,
            )

        return (
            render_template(
                "home.html",
                display_text=[
                    "Invalid Input",
                    str(error),
                ],
            ),
            400,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle 404 errors."""
        logger.warning(
            "Page not found",
            extra={
                "error_type": "not_found",
                "url": request.url,
                "request_id": getattr(g, "request_id", None),
            },
        )

        if request.is_json or request.headers.get("Accept") == "application/json":
            return (
                jsonify(
                    {
                        "error": "Not Found",
                        "message": "The requested resource was not found",
                        "request_id": getattr(g, "request_id", None),
                    }
                ),
                404,
            )

        return (
            render_template(
                "home.html",
                display_text=[
                    "Page Not Found",
                    "The requested page could not be found.",
                ],
            ),
            404,
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors."""
        logger.error(
            "Internal server error occurred",
            extra={
                "error_type": "internal_server_error",
                "error_message": str(error),
                "request_id": getattr(g, "request_id", None),
            },
            exc_info=True,
        )

        if request.is_json or request.headers.get("Accept") == "application/json":
            return (
                jsonify(
                    {
                        "error": "Internal Server Error",
                        "message": "An unexpected error occurred",
                        "request_id": getattr(g, "request_id", None),
                    }
                ),
                500,
            )

        return (
            render_template(
                "home.html",
                display_text=[
                    "Internal Server Error",
                    "An unexpected error occurred. Please try again later.",
                ],
            ),
            500,
        )


def register_health_check(app: Flask) -> None:
    """Register health check endpoint.

    Args:
        app: The Flask application.
    """

    @app.route("/health")
    def health_check():
        """Health check endpoint for monitoring and load balancers."""
        return (
            jsonify(
                {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "version": "1.0.0",
                    "environment": (
                        app.config_instance.ENVIRONMENT
                        if hasattr(app, "config_instance")
                        else "unknown"
                    ),
                }
            ),
            200,
        )

    @app.route("/ready")
    def readiness_check():
        """Readiness check endpoint for Kubernetes deployments."""
        try:
            # Check if container is properly initialized
            if hasattr(app, "container") and app.container:
                return (
                    jsonify(
                        {
                            "status": "ready",
                            "timestamp": time.time(),
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "not_ready",
                            "message": "Application container not initialized",
                        }
                    ),
                    503,
                )
        except Exception as e:
            logger = get_logger(__name__)
            logger.error("Readiness check failed", extra={"error": str(e)})
            return (
                jsonify({"status": "not_ready", "message": "Health check failed"}),
                503,
            )
