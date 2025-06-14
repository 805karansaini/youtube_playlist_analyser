"""Service Factory.

This module provides factory classes for creating service instances.
"""

from core.config import Config
from services.youtube_service import YouTubeService
from services.playlist_analyzer_service import PlaylistAnalyzerService


class ServiceFactory:
    """Factory for creating service instances.

    This class implements the Factory pattern to create and manage service instances.
    It ensures that only one instance of each service is created (Singleton pattern).

    Attributes:
        _instances: A dictionary of service instances.
    """

    _instances = {}

    @classmethod
    def get_youtube_service(cls):
        """Get or create a YouTubeService instance.

        Returns:
            A YouTubeService instance.
        """
        if "youtube_service" not in cls._instances:
            config = Config()
            cls._instances["youtube_service"] = YouTubeService(config)
        return cls._instances["youtube_service"]

    @classmethod
    def get_playlist_analyzer_service(cls):
        """Get or create a PlaylistAnalyzerService instance.

        Returns:
            A PlaylistAnalyzerService instance.
        """
        if "playlist_analyzer_service" not in cls._instances:
            youtube_service = cls.get_youtube_service()
            cls._instances["playlist_analyzer_service"] = PlaylistAnalyzerService(
                youtube_service
            )
        return cls._instances["playlist_analyzer_service"]
