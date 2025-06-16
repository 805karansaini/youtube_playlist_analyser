"""YouTube API Adapter.

This module provides adapter classes for the YouTube API.
"""

from typing import Dict, List
from googleapiclient.discovery import build


class YouTubeApiAdapter:
    """Adapter for the YouTube API.

    This class implements the Adapter pattern to provide a consistent
    interface to the YouTube API. It abstracts the details of the
    YouTube API client and provides methods for retrieving playlist
    and video information.

    Attributes:
        client: The YouTube API client.
    """

    def __init__(self, api_key: str, api_version: str = "v3"):
        """Initialize the YouTubeApiAdapter.

        Args:
            api_key: The YouTube API key.
            api_version: The YouTube API version.
        """
        self.client = build(
            "youtube",
            api_version,
            developerKey=api_key,
            cache_discovery=False,
        )

    def get_playlist_items(
        self, playlist_id: str, max_results: int = 50, page_token: str = ""
    ) -> Dict:
        """Get playlist items from the YouTube API.

        Args:
            playlist_id: The ID of the playlist.
            max_results: The maximum number of results to return.
            page_token: The token for pagination.

        Returns:
            A dictionary containing playlist items information.
        """
        return (
            self.client.playlistItems()
            .list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=max_results,
                pageToken=page_token,
            )
            .execute()
        )

    def get_videos_details(self, video_ids: List[str]) -> Dict:
        """Get video details from the YouTube API.

        Args:
            video_ids: A list of video IDs.

        Returns:
            A dictionary containing video details.
        """
        return (
            self.client.videos()
            .list(part="contentDetails,snippet", id=",".join(video_ids))
            .execute()
        )
