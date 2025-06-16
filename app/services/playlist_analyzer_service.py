"""Playlist Analyzer Service.

This module provides services for analyzing YouTube playlists, including
calculating statistics and preparing data for visualization.
"""

import logging
from typing import Dict, Any
from exceptions.exception import PlaylistAnalysisError
from strategies.analysis_strategy import AnalysisStrategy, StandardAnalysisStrategy


class PlaylistAnalyzerService:
    """Service for analyzing YouTube playlists.

    This service handles the business logic for analyzing YouTube playlists,
    including calculating statistics and preparing data for visualization.
    It uses the Strategy pattern to support different analysis strategies.

    Attributes:
        youtube_service: The YouTube service for interacting with the YouTube API.
        strategy: The analysis strategy to use.
        logger: The logger to use.
    """

    def __init__(self, youtube_service, strategy: AnalysisStrategy = None):
        """Initialize the PlaylistAnalyzerService.

        Args:
            youtube_service: The YouTube service for interacting with the YouTube API.
            strategy: The analysis strategy to use. If None, a StandardAnalysisStrategy is used.
        """
        self.youtube_service = youtube_service
        self.strategy = strategy or StandardAnalysisStrategy()
        self.logger = logging.getLogger(__name__)

    def set_strategy(self, strategy: AnalysisStrategy) -> None:
        """Set the analysis strategy.

        Args:
            strategy: The analysis strategy to use.
        """
        self.strategy = strategy

    def analyze_playlist(self, playlist_url: str) -> Dict[str, Any]:
        """Analyze a YouTube playlist.

        Args:
            playlist_url: The URL of the YouTube playlist to analyze.

        Returns:
            A dictionary containing the analysis results, including chart data and display text.

        Raises:
            YouTubeApiError: If there's an error with the YouTube API.
            PlaylistAnalysisError: If there's an error analyzing the playlist.
        """
        try:
            # Extract playlist ID
            playlist_id = self.youtube_service.extract_playlist_id(playlist_url)

            # Get playlist details
            video_count, total_seconds, videos = (
                self.youtube_service.get_playlist_details(playlist_id)
            )

            # Analyze playlist using the strategy, passing playlist_id
            return self.strategy.analyze(
                videos, total_seconds, video_count, playlist_id
            )

        except Exception as e:
            self.logger.error(f"Error analyzing playlist: {str(e)}")
            raise PlaylistAnalysisError(f"Error analyzing playlist: {str(e)}", cause=e)
