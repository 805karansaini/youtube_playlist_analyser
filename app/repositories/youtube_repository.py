"""YouTube Repository.

This module provides repository classes for accessing YouTube data.
"""

from typing import Dict, List


class YouTubeRepository:
    """Repository for accessing YouTube data.

    This class implements the Repository pattern to abstract data access
    from the business logic. It provides methods for retrieving playlist
    and video information from the YouTube API.

    Attributes:
        youtube_client: The YouTube API client.
    """

    def __init__(self, youtube_client):
        """Initialize the YouTubeRepository.

        Args:
            youtube_client: The YouTube API client.
        """
        self.youtube_client = youtube_client

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
            self.youtube_client.playlistItems()
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
            self.youtube_client.videos()
            .list(part="contentDetails,snippet", id=",".join(video_ids))
            .execute()
        )
