"""Analysis Strategy.

This module provides strategy classes for different types of playlist analysis.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class AnalysisStrategy(ABC):
    """Abstract base class for analysis strategies.

    This class defines the interface for analysis strategies.
    Different strategies can be implemented by subclassing this class.
    """

    @abstractmethod
    def analyze(
        self,
        videos: List[Dict],
        total_seconds: float,
        video_count: int,
        playlist_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze playlist data.

        Args:
            videos: A list of video information dictionaries.
            total_seconds: The total duration of the playlist in seconds.
            video_count: The number of videos in the playlist.
            playlist_id: The playlist ID (optional).

        Returns:
            A dictionary containing the analysis results.
        """
        pass


class StandardAnalysisStrategy(AnalysisStrategy):
    """Standard analysis strategy.

    This strategy provides standard analysis of playlist data,
    including video count, average length, total duration, and
    playback speed calculations.
    """

    def analyze(
        self,
        videos: List[Dict],
        total_seconds: float,
        video_count: int,
        playlist_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze playlist data using the standard strategy.

        Args:
            videos: A list of video information dictionaries.
            total_seconds: The total duration of the playlist in seconds.
            video_count: The number of videos in the playlist.
            playlist_id: The playlist ID (optional).

        Returns:
            A dictionary containing chart data, display text, and analysis data.
        """
        from helper.utils import format_duration

        # Calculate additional metrics
        average_duration = total_seconds / video_count if video_count > 0 else 0

        # Sort videos by duration to find longest and shortest
        sorted_videos = sorted(
            videos, key=lambda x: x.get("duration_seconds", x.get("duration_minutes", 0) * 60), reverse=True
        )
        longest_video = (
            sorted_videos[0]
            if sorted_videos
            else {"title": "N/A", "duration_seconds": 0}
        )
        shortest_video = (
            sorted_videos[-1]
            if sorted_videos
            else {"title": "N/A", "duration_seconds": 0}
        )

        # Calculate playback time at different speeds
        playback_speeds = {
            "1.25x": total_seconds / 1.25,
            "1.50x": total_seconds / 1.50,
            "1.75x": total_seconds / 1.75,
            "2.00x": total_seconds / 2.00,
        }

        # Build comprehensive analysis data structure for export compatibility
        analysis_data = {
            "playlist_id": playlist_id,
            "analysis_type": "basic",
            "video_count": video_count,
            "total_duration": format_duration(total_seconds),
            "total_duration_seconds": total_seconds,
            "average_duration": format_duration(average_duration),
            "average_duration_seconds": average_duration,
            "total_views": sum(video.get("view_count", 0) for video in videos),
            "total_likes": sum(video.get("like_count", 0) for video in videos),
            "total_comments": sum(video.get("comment_count", 0) for video in videos),
            "longest_video": {
                "title": longest_video.get("title", "N/A"),
                "duration": format_duration(longest_video.get("duration_seconds", longest_video.get("duration_minutes", 0) * 60)),
            },
            "shortest_video": {
                "title": shortest_video.get("title", "N/A"),
                "duration": format_duration(shortest_video.get("duration_seconds", shortest_video.get("duration_minutes", 0) * 60)),
            },
            "playback_speeds": {
                speed: format_duration(duration)
                for speed, duration in playback_speeds.items()
            },
            "videos": videos,
            "channels": list(
                set(
                    video.get("channel_title", "")
                    for video in videos
                    if video.get("channel_title")
                )
            ),
            "created_at": None,  # Would need playlist metadata
            "summary": f"Analysis of {video_count} videos with total duration of {format_duration(total_seconds)}. Average video length is {format_duration(average_duration)}.",
        }

        return {
            "chart_data": [
                [video.get("title", "") for video in videos],
                [video.get("duration_seconds", video.get("duration_minutes", 0) * 60) / 60 for video in videos],
            ],
            "display_text": [
                f"No of videos: {video_count}",
                f"Average length of a video: {format_duration(total_seconds/video_count)}",
                f"Total length of playlist: {format_duration(total_seconds)}",
                f"At 1.25x: {format_duration(total_seconds/1.25)}",
                f"At 1.50x: {format_duration(total_seconds/1.50)}",
                f"At 1.75x: {format_duration(total_seconds/1.75)}",
                f"At 2.00x: {format_duration(total_seconds/2.00)}",
            ],
            "analysis_data": analysis_data,
            # Add export-friendly top-level fields for backward compatibility
            "playlist_id": playlist_id,
            "analysis_type": "basic",
            "video_count": video_count,
            "total_duration": format_duration(total_seconds),
            "average_duration": format_duration(average_duration),
            "total_views": analysis_data["total_views"],
            "total_likes": analysis_data["total_likes"],
            "total_comments": analysis_data["total_comments"],
            "videos": videos,
            "summary": analysis_data["summary"],
        }
