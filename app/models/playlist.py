"""Playlist Model.

This module provides model classes for representing playlists with enhanced analytics.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from statistics import median, stdev
from pydantic import BaseModel, Field, validator
from .video import Video


class Playlist(BaseModel):
    """Model class for representing a playlist with comprehensive analytics.

    This class represents a playlist with its metadata and video collection,
    providing advanced analytics and insights about the playlist content.

    Attributes:
        playlist_id: The unique ID of the playlist.
        title: The title of the playlist (optional).
        description: The playlist description (optional).
        videos: The videos in the playlist.
        created_at: When the playlist was created (optional).
        updated_at: When the playlist was last updated (optional).
    """

    playlist_id: str = Field(..., min_length=1, description="YouTube playlist ID")
    title: Optional[str] = Field(default=None, description="Playlist title")
    description: Optional[str] = Field(default=None, description="Playlist description")
    videos: List[Video] = Field(default_factory=list, description="Videos in playlist")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
        extra = "forbid"

    @validator("videos")
    def validate_videos_list(cls, v):
        """Validate videos list."""
        if len(v) > 1000:  # Reasonable limit
            raise ValueError("Playlist cannot contain more than 1000 videos")
        return v

    @property
    def video_count(self) -> int:
        """Get the number of videos in the playlist.

        Returns:
            The number of videos in the playlist.
        """
        return len(self.videos)

    @property
    def total_seconds(self) -> float:
        """Get the total duration of the playlist in seconds.

        Returns:
            The total duration of the playlist in seconds.
        """
        return sum(video.duration_seconds for video in self.videos)

    @property
    def total_minutes(self) -> float:
        """Get the total duration of the playlist in minutes.

        Returns:
            The total duration of the playlist in minutes.
        """
        return self.total_seconds / 60

    @property
    def total_hours(self) -> float:
        """Get the total duration of the playlist in hours.

        Returns:
            The total duration of the playlist in hours.
        """
        return self.total_seconds / 3600

    @property
    def average_duration(self) -> float:
        """Get the average duration of videos in the playlist.

        Returns:
            The average duration of videos in the playlist in seconds.
            Returns 0 if the playlist is empty.
        """
        if not self.videos:
            return 0
        return self.total_seconds / self.video_count

    @property
    def median_duration(self) -> float:
        """Get the median duration of videos in the playlist.

        Returns:
            The median duration in seconds, or 0 if empty.
        """
        if not self.videos:
            return 0
        durations = [video.duration_seconds for video in self.videos]
        return median(durations)

    @property
    def duration_std_dev(self) -> float:
        """Get the standard deviation of video durations.

        Returns:
            The standard deviation in seconds, or 0 if insufficient data.
        """
        if len(self.videos) < 2:
            return 0
        durations = [video.duration_seconds for video in self.videos]
        return stdev(durations)

    @property
    def total_views(self) -> int:
        """Get the total view count across all videos.

        Returns:
            Total views for all videos in the playlist.
        """
        return sum(video.view_count for video in self.videos)

    @property
    def total_likes(self) -> int:
        """Get the total like count across all videos.

        Returns:
            Total likes for all videos in the playlist.
        """
        return sum(video.like_count for video in self.videos)

    @property
    def total_comments(self) -> int:
        """Get the total comment count across all videos.

        Returns:
            Total comments for all videos in the playlist.
        """
        return sum(video.comment_count for video in self.videos)

    @property
    def average_engagement_rate(self) -> float:
        """Get the average engagement rate across all videos.

        Returns:
            Average engagement rate as a percentage.
        """
        if not self.videos:
            return 0.0
        engagement_rates = [video.engagement_rate for video in self.videos]
        return sum(engagement_rates) / len(engagement_rates)

    @property
    def unique_channels(self) -> List[str]:
        """Get list of unique channels in the playlist.

        Returns:
            List of unique channel titles.
        """
        channels = set()
        for video in self.videos:
            if video.channel_title:
                channels.add(video.channel_title)
        return sorted(list(channels))

    @property
    def channel_distribution(self) -> Dict[str, int]:
        """Get distribution of videos by channel.

        Returns:
            Dictionary mapping channel names to video counts.
        """
        distribution = {}
        for video in self.videos:
            channel = video.channel_title or "Unknown"
            distribution[channel] = distribution.get(channel, 0) + 1
        return distribution

    @property
    def longest_video(self) -> Optional[Video]:
        """Get the longest video in the playlist.

        Returns:
            Video object with the longest duration, or None if empty.
        """
        if not self.videos:
            return None
        return max(self.videos, key=lambda v: v.duration_seconds)

    @property
    def shortest_video(self) -> Optional[Video]:
        """Get the shortest video in the playlist.

        Returns:
            Video object with the shortest duration, or None if empty.
        """
        if not self.videos:
            return None
        return min(self.videos, key=lambda v: v.duration_seconds)

    @property
    def most_viewed_video(self) -> Optional[Video]:
        """Get the most viewed video in the playlist.

        Returns:
            Video object with the highest view count, or None if empty.
        """
        if not self.videos:
            return None
        return max(self.videos, key=lambda v: v.view_count)

    def get_videos_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Video]:
        """Get videos published within a date range.

        Args:
            start_date: Start of the date range.
            end_date: End of the date range.

        Returns:
            List of videos published within the date range.
        """
        filtered_videos = []
        for video in self.videos:
            if video.published_date:
                if start_date <= video.published_date <= end_date:
                    filtered_videos.append(video)
        return filtered_videos

    def get_top_videos_by_views(self, limit: int = 10) -> List[Video]:
        """Get top videos sorted by view count.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of top videos by view count.
        """
        return sorted(self.videos, key=lambda v: v.view_count, reverse=True)[:limit]

    def get_top_videos_by_engagement(self, limit: int = 10) -> List[Video]:
        """Get top videos sorted by engagement rate.

        Args:
            limit: Maximum number of videos to return.

        Returns:
            List of top videos by engagement rate.
        """
        return sorted(self.videos, key=lambda v: v.engagement_rate, reverse=True)[
            :limit
        ]

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive analytics summary.

        Returns:
            Dictionary containing comprehensive playlist analytics.
        """
        return {
            "playlist_id": self.playlist_id,
            "title": self.title,
            "video_count": self.video_count,
            "total_duration_seconds": self.total_seconds,
            "total_duration_hours": round(self.total_hours, 2),
            "average_duration_minutes": round(self.average_duration / 60, 2),
            "median_duration_minutes": round(self.median_duration / 60, 2),
            "duration_std_dev_minutes": round(self.duration_std_dev / 60, 2),
            "total_views": self.total_views,
            "total_likes": self.total_likes,
            "total_comments": self.total_comments,
            "average_engagement_rate": round(self.average_engagement_rate, 2),
            "unique_channels_count": len(self.unique_channels),
            "channel_distribution": self.channel_distribution,
            "longest_video_duration_minutes": (
                round(self.longest_video.duration_minutes, 2)
                if self.longest_video
                else 0
            ),
            "shortest_video_duration_minutes": (
                round(self.shortest_video.duration_minutes, 2)
                if self.shortest_video
                else 0
            ),
            "most_viewed_video_views": (
                self.most_viewed_video.view_count if self.most_viewed_video else 0
            ),
        }
