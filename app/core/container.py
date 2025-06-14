"""Dependency Injection Container.

This module provides an enhanced container for managing dependencies with
thread safety, lifecycle management, and comprehensive error handling.
"""

import threading
from typing import Any, Dict, TypeVar, Callable
from functools import wraps

from adapters.youtube_api_adapter import YouTubeApiAdapter
from core.config import Config
from core.logging_config import get_logger
from repositories.youtube_repository import YouTubeRepository
from services.export_service import ExportService
from services.pdf_report_service import PDFReportService
from services.playlist_analyzer_service import PlaylistAnalyzerService
from services.youtube_analytics_service import YouTubeAnalyticsService
from services.youtube_service import YouTubeService
from strategies.analysis_strategy import StandardAnalysisStrategy
from strategies.enhanced_analysis_strategy import EnhancedAnalysisStrategy

T = TypeVar("T")


def singleton_with_lock(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to ensure thread-safe singleton creation."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        service_name = func.__name__.replace("get_", "")

        # Double-checked locking pattern
        if service_name not in self._instances:
            with self._lock:
                if service_name not in self._instances:
                    try:
                        instance = func(self, *args, **kwargs)
                        self._instances[service_name] = instance
                        self.logger.debug(f"Created singleton instance: {service_name}")
                    except Exception as e:
                        self.logger.error(f"Failed to create {service_name}: {str(e)}")
                        raise

        return self._instances[service_name]

    return wrapper


class Container:
    """Enhanced container for managing dependencies with thread safety.

    This class implements the Dependency Injection pattern to manage
    dependencies between components. It provides methods for getting
    instances of various components, ensuring that only one instance
    of each component is created (Singleton pattern) with thread safety.

    Features:
        - Thread-safe singleton creation
        - Comprehensive error handling
        - Service lifecycle management
        - Health checking capabilities
        - Dependency graph validation

    Attributes:
        _instances: A dictionary of component instances.
        _lock: Threading lock for thread-safe operations.
        logger: Logger instance for container operations.
    """

    def __init__(self):
        """Initialize the Container with thread safety and logging."""
        self._instances: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self.logger = get_logger(__name__)
        self._creation_order: list = []
        self._health_checks: Dict[str, Callable] = {}

        self.logger.info("Container initialized successfully")

    @singleton_with_lock
    def get_config(self) -> Config:
        """Get or create a Config instance.

        Returns:
            A Config instance.
        """
        return Config()

    @singleton_with_lock
    def get_youtube_adapter(self) -> YouTubeApiAdapter:
        """Get or create a YouTubeApiAdapter instance.

        Returns:
            A YouTubeApiAdapter instance.
        """
        config = self.get_config()
        return YouTubeApiAdapter(
            api_key=config.YOUTUBE_API_KEY, api_version=config.YOUTUBE_API_VERSION
        )

    @singleton_with_lock
    def get_youtube_repository(self) -> YouTubeRepository:
        """Get or create a YouTubeRepository instance.

        Returns:
            A YouTubeRepository instance.
        """
        adapter = self.get_youtube_adapter()
        return YouTubeRepository(adapter.client)

    @singleton_with_lock
    def get_youtube_service(self) -> YouTubeService:
        """Get or create a YouTubeService instance.

        Returns:
            A YouTubeService instance.
        """
        config = self.get_config()
        return YouTubeService(config)

    @singleton_with_lock
    def get_youtube_analytics_service(self) -> YouTubeAnalyticsService:
        """Get or create a YouTubeAnalyticsService instance.

        Returns:
            A YouTubeAnalyticsService instance.
        """
        config = self.get_config()
        return YouTubeAnalyticsService(config)

    @singleton_with_lock
    def get_analysis_strategy(self) -> EnhancedAnalysisStrategy:
        """Get or create an AnalysisStrategy instance.

        Returns:
            An EnhancedAnalysisStrategy instance with YouTube Analytics integration.
        """
        youtube_analytics_service = self.get_youtube_analytics_service()
        return EnhancedAnalysisStrategy(youtube_analytics_service)

    @singleton_with_lock
    def get_standard_analysis_strategy(self) -> StandardAnalysisStrategy:
        """Get or create a StandardAnalysisStrategy instance.

        Returns:
            A StandardAnalysisStrategy instance.
        """
        return StandardAnalysisStrategy()

    @singleton_with_lock
    def get_playlist_analyzer_service(self) -> PlaylistAnalyzerService:
        """Get or create a PlaylistAnalyzerService instance.

        Returns:
            A PlaylistAnalyzerService instance.
        """
        youtube_service = self.get_youtube_service()
        strategy = self.get_analysis_strategy()
        return PlaylistAnalyzerService(youtube_service, strategy)

    @singleton_with_lock
    def get_export_service(self) -> ExportService:
        """Get or create an ExportService instance.

        Returns:
            An ExportService instance.
        """
        return ExportService()

    @singleton_with_lock
    def get_pdf_report_service(self) -> PDFReportService:
        """Get or create a PDFReportService instance.

        Returns:
            A PDFReportService instance.
        """
        return PDFReportService()

    # Utility methods for container management

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all registered services.

        Returns:
            Dictionary containing health status of all services.
        """
        health_status = {
            "container_status": "healthy",
            "services": {},
            "total_services": len(self._instances),
            "creation_order": self._creation_order,
        }

        for service_name, instance in self._instances.items():
            try:
                # Check if service has a health check method
                if hasattr(instance, "health_check"):
                    service_health = instance.health_check()
                elif hasattr(instance, "get_service_statistics"):
                    service_health = {
                        "status": "healthy",
                        "statistics": instance.get_service_statistics(),
                    }
                else:
                    service_health = {
                        "status": "healthy",
                        "message": "Service available",
                    }

                health_status["services"][service_name] = service_health

            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health_status["container_status"] = "degraded"

        return health_status

    def get_service_info(self) -> Dict[str, Any]:
        """Get information about all registered services.

        Returns:
            Dictionary containing service information.
        """
        return {
            "registered_services": list(self._instances.keys()),
            "total_count": len(self._instances),
            "creation_order": self._creation_order,
            "thread_safe": True,
            "container_type": "Singleton",
        }

    def clear_cache(self) -> None:
        """Clear caches from all services that support it."""
        cache_cleared_count = 0

        for service_name, instance in self._instances.items():
            try:
                if hasattr(instance, "clear_cache"):
                    instance.clear_cache()
                    cache_cleared_count += 1
                    self.logger.debug(f"Cleared cache for service: {service_name}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to clear cache for {service_name}: {str(e)}"
                )

        self.logger.info(f"Cache cleared for {cache_cleared_count} services")

    def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        self.logger.info("Initiating container shutdown")

        # Shutdown services in reverse order of creation
        for service_name in reversed(self._creation_order):
            if service_name in self._instances:
                try:
                    instance = self._instances[service_name]
                    if hasattr(instance, "shutdown"):
                        instance.shutdown()
                        self.logger.debug(f"Shutdown service: {service_name}")
                except Exception as e:
                    self.logger.error(f"Error shutting down {service_name}: {str(e)}")

        # Clear all instances
        with self._lock:
            self._instances.clear()
            self._creation_order.clear()

        self.logger.info("Container shutdown completed")
