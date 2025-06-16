"""Enhanced Analysis Strategy with YouTube Analytics API integration.

This module provides an enhanced analysis strategy that uses the YouTube Analytics API
to provide comprehensive insights including engagement metrics, view distribution,
top videos analysis, and timeline data.
"""

import logging
from typing import Any, Dict, List, Optional

from strategies.analysis_strategy import AnalysisStrategy


class EnhancedAnalysisStrategy(AnalysisStrategy):
    """Enhanced analysis strategy with YouTube Analytics API integration.

    This strategy provides comprehensive analysis of playlist data including:
    - Standard metrics (duration, video count)
    - Advanced engagement metrics (views, likes, comments, engagement rates)
    - Top videos analysis by different criteria
    - View distribution and concentration analysis
    - Timeline analysis and trends
    - Visual analytics data for charts and graphs
    """

    def __init__(self, youtube_analytics_service=None):
        """Initialize the Enhanced Analysis Strategy.

        Args:
            youtube_analytics_service: Service for YouTube Analytics API calls
        """
        self.youtube_analytics_service = youtube_analytics_service
        self.logger = logging.getLogger(__name__)

    def analyze(
        self,
        videos: List[Dict],
        total_seconds: float,
        video_count: int,
        playlist_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze playlist data using enhanced analytics.

        Args:
            videos: A list of video information dictionaries with comprehensive metadata
            total_seconds: The total duration of the playlist in seconds
            video_count: The number of videos in the playlist
            playlist_id: The playlist ID

        Returns:
            A dictionary containing comprehensive analysis results with visual analytics data
        """

        # Get basic analysis first
        basic_analysis = self._get_basic_analysis(
            videos, total_seconds, video_count, playlist_id or ""
        )

        # If we have analytics service, get enhanced analytics
        if self.youtube_analytics_service and videos:
            try:
                video_ids = [
                    video.get("video_id", "")
                    for video in videos
                    if video.get("video_id")
                ]
                analytics_data = self.youtube_analytics_service.get_playlist_analytics(
                    playlist_id or "", video_ids
                )

                # Merge basic analysis with analytics data
                enhanced_analysis = self._merge_analytics_data(
                    basic_analysis, analytics_data
                )
                return enhanced_analysis

            except Exception as e:
                self.logger.warning(
                    f"Failed to get analytics data: {str(e)}. Falling back to basic analysis."
                )

        # Return basic analysis if analytics unavailable
        return basic_analysis

    def _get_basic_analysis(
        self,
        videos: List[Dict],
        total_seconds: float,
        video_count: int,
        playlist_id: str,
    ) -> Dict[str, Any]:
        """Get basic analysis similar to StandardAnalysisStrategy.

        Args:
            videos: List of video dictionaries
            total_seconds: Total duration in seconds
            video_count: Number of videos
            playlist_id: Playlist ID

        Returns:
            Dict containing basic analysis data
        """
        from helper.utils import format_duration

        # Calculate additional metrics
        average_duration = total_seconds / video_count if video_count > 0 else 0

        # Sort videos by duration to find longest and shortest
        sorted_videos = sorted(
            videos, key=lambda x: x.get("duration_seconds", 0), reverse=True
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

        # Calculate totals from video data
        total_views = sum(video.get("view_count", 0) for video in videos)
        total_likes = sum(video.get("like_count", 0) for video in videos)
        total_comments = sum(video.get("comment_count", 0) for video in videos)

        # Build analysis data structure
        analysis_data = {
            "playlist_id": playlist_id,
            "analysis_type": "enhanced",
            "video_count": video_count,
            "total_duration": format_duration(total_seconds),
            "total_duration_seconds": total_seconds,
            "average_duration": format_duration(average_duration),
            "average_duration_seconds": average_duration,
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "longest_video": {
                "title": longest_video.get("title", "N/A"),
                "duration": format_duration(longest_video.get("duration_seconds", 0)),
            },
            "shortest_video": {
                "title": shortest_video.get("title", "N/A"),
                "duration": format_duration(shortest_video.get("duration_seconds", 0)),
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
            "summary": f"Enhanced analysis of {video_count} videos with {total_views:,} total views and {total_likes:,} total likes.",
        }

        return {
            "chart_data": [
                [video.get("title", "") for video in videos],
                [
                    video.get("duration_seconds", 0) / 60 for video in videos
                ],  # Convert to minutes for chart
            ],
            "display_text": [
                f"No of videos: {video_count}",
                f"Total views: {total_views:,}",
                f"Total likes: {total_likes:,}",
                f"Total comments: {total_comments:,}",
                f"Average length: {format_duration(average_duration)}",
                f"Total duration: {format_duration(total_seconds)}",
                f"At 1.25x: {format_duration(total_seconds / 1.25)}",
                f"At 1.50x: {format_duration(total_seconds / 1.50)}",
                f"At 2.00x: {format_duration(total_seconds / 2.00)}",
            ],
            "analysis_data": analysis_data,
            # Top-level fields for backward compatibility
            "playlist_id": playlist_id,
            "video_count": video_count,
            "total_duration": format_duration(total_seconds),
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
        }

    def _merge_analytics_data(
        self, basic_analysis: Dict[str, Any], analytics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge basic analysis with YouTube Analytics data.

        Args:
            basic_analysis: Basic analysis results
            analytics_data: Analytics data from YouTube Analytics API

        Returns:
            Dict containing merged comprehensive analysis
        """
        # Get analytics metrics
        total_metrics = analytics_data.get("total_metrics", {})
        top_videos = analytics_data.get("top_videos", {})
        engagement_data = analytics_data.get("engagement_data", {})
        view_distribution = analytics_data.get("view_distribution", {})
        timeline_data = analytics_data.get("timeline_data", {})

        # Update analysis data with analytics insights
        enhanced_analysis_data = basic_analysis["analysis_data"].copy()
        enhanced_analysis_data.update(
            {
                "analytics_available": True,
                "engagement_metrics": {
                    "average_engagement_rate": total_metrics.get(
                        "average_engagement_rate", 0
                    ),
                    "like_ratio": engagement_data.get("average_like_ratio", 0),
                    "comment_ratio": engagement_data.get("average_comment_ratio", 0),
                    "high_engagement_videos": engagement_data.get(
                        "high_engagement_videos", 0
                    ),
                    "low_engagement_videos": engagement_data.get(
                        "low_engagement_videos", 0
                    ),
                },
                "view_insights": {
                    "concentration_ratio": view_distribution.get(
                        "concentration_ratio", 0
                    ),
                    "top_video_share": view_distribution.get("top_video_share", 0),
                    "view_trend": timeline_data.get("view_trend", "stable"),
                    "most_productive_month": timeline_data.get(
                        "most_productive_month", "N/A"
                    ),
                },
                "top_performers": {
                    "by_views": top_videos.get("by_views", [])[:5],  # Top 5 for display
                    "by_likes": top_videos.get("by_likes", [])[:5],
                    "by_engagement": top_videos.get("by_engagement", [])[:5],
                },
            }
        )

        # Create visual analytics data
        visual_analytics = self._create_visual_analytics_data(analytics_data)

        # Enhanced display text with analytics insights
        enhanced_display_text = basic_analysis["display_text"].copy()
        enhanced_display_text.extend(
            [
                f"Average engagement rate: {total_metrics.get('average_engagement_rate', 0):.2f}%",
                f"View concentration: {view_distribution.get('concentration_ratio', 0):.1f}% in top 20% videos",
                f"Performance trend: {timeline_data.get('view_trend', 'stable').title()}",
            ]
        )

        return {
            **basic_analysis,
            "analysis_data": enhanced_analysis_data,
            "display_text": enhanced_display_text,
            "visual_analytics": visual_analytics,
            "analytics_available": True,
        }

    def _create_visual_analytics_data(
        self, analytics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create visual analytics data for charts and graphs.

        Args:
            analytics_data: Raw analytics data from YouTube Analytics API

        Returns:
            Dict containing structured data for visual components
        """
        top_videos = analytics_data.get("top_videos", {})
        engagement_data = analytics_data.get("engagement_data", {})
        view_distribution = analytics_data.get("view_distribution", {})
        timeline_data = analytics_data.get("timeline_data", {})

        return {
            "top_videos": {
                "by_views": {
                    "labels": [
                        (
                            video.get("title", "")[:30] + "..."
                            if len(video.get("title", "")) > 30
                            else video.get("title", "")
                        )
                        for video in top_videos.get("by_views", [])[:10]
                    ],
                    "data": [
                        video.get("view_count", 0)
                        for video in top_videos.get("by_views", [])[:10]
                    ],
                    "type": "bar",
                    "title": "Top Videos by Views",
                },
                "by_engagement": {
                    "labels": [
                        (
                            video.get("title", "")[:30] + "..."
                            if len(video.get("title", "")) > 30
                            else video.get("title", "")
                        )
                        for video in top_videos.get("by_engagement", [])[:10]
                    ],
                    "data": [
                        video.get("engagement_rate", 0)
                        for video in top_videos.get("by_engagement", [])[:10]
                    ],
                    "type": "bar",
                    "title": "Top Videos by Engagement Rate (%)",
                },
            },
            "engagement": {
                "overview": {
                    "labels": [
                        "High Engagement",
                        "Medium Engagement",
                        "Low Engagement",
                    ],
                    "data": [
                        engagement_data.get("high_engagement_videos", 0),
                        analytics_data.get("total_metrics", {}).get("video_count", 0)
                        - engagement_data.get("high_engagement_videos", 0)
                        - engagement_data.get("low_engagement_videos", 0),
                        engagement_data.get("low_engagement_videos", 0),
                    ],
                    "type": "doughnut",
                    "title": "Engagement Distribution",
                },
                "metrics": {
                    "like_ratio": engagement_data.get("average_like_ratio", 0),
                    "comment_ratio": engagement_data.get("average_comment_ratio", 0),
                    "avg_engagement": analytics_data.get("total_metrics", {}).get(
                        "average_engagement_rate", 0
                    ),
                },
            },
            "view_distribution": {
                "chart": {
                    "labels": [
                        (
                            item.get("title", "")[:20] + "..."
                            if len(item.get("title", "")) > 20
                            else item.get("title", "")
                        )
                        for item in view_distribution.get("distribution", [])[:15]
                    ],
                    "data": [
                        item.get("percentage", 0)
                        for item in view_distribution.get("distribution", [])[:15]
                    ],
                    "type": "pie",
                    "title": "View Distribution Across Videos",
                },
                "concentration": view_distribution.get("concentration_ratio", 0),
                "top_video_share": view_distribution.get("top_video_share", 0),
            },
            "timeline": {
                "chart": {
                    "labels": [
                        item.get("month", "")
                        for item in timeline_data.get("timeline", [])
                    ],
                    "datasets": [
                        {
                            "label": "Views",
                            "data": [
                                item.get("total_views", 0)
                                for item in timeline_data.get("timeline", [])
                            ],
                            "borderColor": "rgb(54, 162, 235)",
                            "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        },
                        {
                            "label": "Video Count",
                            "data": [
                                item.get("video_count", 0)
                                for item in timeline_data.get("timeline", [])
                            ],
                            "borderColor": "rgb(255, 99, 132)",
                            "backgroundColor": "rgba(255, 99, 132, 0.2)",
                            "yAxisID": "y1",
                        },
                    ],
                    "type": "line",
                    "title": "Timeline Analysis",
                },
                "trend": timeline_data.get("view_trend", "stable"),
                "date_range": timeline_data.get("date_range", {}),
                "most_productive_month": timeline_data.get(
                    "most_productive_month", "N/A"
                ),
            },
        }
