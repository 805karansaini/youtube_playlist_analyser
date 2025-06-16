"""YouTube Analytics Service for advanced metrics and insights.

This service handles interactions with the YouTube Analytics API to retrieve
detailed analytics data including view counts, engagement metrics, revenue data,
and time-based analytics for playlists and videos.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from core.config import Config
from googleapiclient.discovery import build


class YouTubeAnalyticsService:
    """Service class for handling YouTube Analytics API interactions.

    This class provides methods to retrieve advanced analytics data including:
    - Video engagement metrics (views, likes, comments, shares)
    - Time-based analytics and trends
    - Geographic and demographic data
    - Revenue and monetization metrics (for eligible channels)
    """

    def __init__(self, config: Config):
        """Initialize YouTubeAnalyticsService with configuration.

        Args:
            config (Config): Configuration object containing YouTube API settings.
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # Build YouTube Analytics API service
        self.youtube_analytics = build(
            "youtubeAnalytics",
            "v2",
            developerKey=config.YOUTUBE_API_KEY,
            cache_discovery=False,
        )

        # Also maintain regular YouTube API for metadata
        self.youtube = build(
            "youtube",
            config.YOUTUBE_API_VERSION,
            developerKey=config.YOUTUBE_API_KEY,
            cache_discovery=False,
        )

    def get_playlist_analytics(
        self, playlist_id: str, video_ids: List[str]
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a playlist.

        Args:
            playlist_id (str): YouTube playlist ID
            video_ids (List[str]): List of video IDs in the playlist

        Returns:
            Dict containing analytics data:
            - total_metrics: Aggregated view counts, likes, comments
            - top_videos: Top performing videos by various metrics
            - engagement_data: Engagement rates and interaction metrics
            - view_distribution: Distribution of views across videos
            - timeline_data: Time-based view patterns
        """
        try:
            # Get basic video statistics for all videos
            video_stats = self._get_video_statistics(video_ids)

            # Calculate aggregated metrics
            total_metrics = self._calculate_total_metrics(video_stats)

            # Get top performing videos
            top_videos = self._get_top_videos(video_stats)

            # Calculate engagement metrics
            engagement_data = self._calculate_engagement_metrics(video_stats)

            # Get view distribution data
            view_distribution = self._calculate_view_distribution(video_stats)

            # Get timeline data (publish dates and view trends)
            timeline_data = self._get_timeline_data(video_stats)

            return {
                "total_metrics": total_metrics,
                "top_videos": top_videos,
                "engagement_data": engagement_data,
                "view_distribution": view_distribution,
                "timeline_data": timeline_data,
                "raw_video_stats": video_stats,
            }

        except Exception as e:
            self.logger.error(f"Error getting playlist analytics: {str(e)}")
            return self._get_empty_analytics()

    def _get_video_statistics(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get statistics for multiple videos.

        Args:
            video_ids (List[str]): List of video IDs

        Returns:
            List of video statistics dictionaries
        """
        video_stats = []

        # Process videos in batches of 50 (API limit)
        batch_size = 50
        for i in range(0, len(video_ids), batch_size):
            batch_ids = video_ids[i : i + batch_size]

            try:
                response = (
                    self.youtube.videos()
                    .list(
                        part="statistics,snippet,contentDetails", id=",".join(batch_ids)
                    )
                    .execute()
                )

                for video in response.get("items", []):
                    stats = self._extract_video_analytics(video)
                    if stats:
                        video_stats.append(stats)

            except Exception as e:
                self.logger.warning(f"Error fetching batch statistics: {str(e)}")
                continue

        return video_stats

    def _extract_video_analytics(self, video: Dict) -> Dict[str, Any]:
        """Extract analytics data from video API response.

        Args:
            video (Dict): Video data from YouTube API

        Returns:
            Dict containing extracted analytics data
        """
        try:
            video_id = video.get("id", "")
            snippet = video.get("snippet", {})
            statistics = video.get("statistics", {})
            content_details = video.get("contentDetails", {})

            # Parse statistics with safe defaults
            view_count = int(statistics.get("viewCount", 0) or 0)
            like_count = int(statistics.get("likeCount", 0) or 0)
            comment_count = int(statistics.get("commentCount", 0) or 0)

            # Calculate engagement rate
            engagement_rate = 0
            if view_count > 0:
                total_engagement = like_count + comment_count
                engagement_rate = (total_engagement / view_count) * 100

            # Parse duration
            duration_str = content_details.get("duration", "PT0S")
            duration_seconds = self._parse_duration_to_seconds(duration_str)

            # Parse publish date
            published_at = snippet.get("publishedAt", "")
            publish_date = None
            if published_at:
                try:
                    publish_date = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )
                except Exception as e:
                    self.logger.error(f"Error parsing publish date: {str(e)}")
                    publish_date = None

            return {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": publish_date,
                "duration_seconds": duration_seconds,
                "view_count": view_count,
                "like_count": like_count,
                "comment_count": comment_count,
                "engagement_rate": round(engagement_rate, 2),
                "thumbnail_url": snippet.get("thumbnails", {})
                .get("medium", {})
                .get("url", ""),
                "description": (
                    snippet.get("description", "")[:200]
                    if snippet.get("description")
                    else ""
                ),
            }

        except Exception as e:
            self.logger.warning(f"Error extracting video analytics: {str(e)}")
            return {}

    def _parse_duration_to_seconds(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to seconds.

        Args:
            duration_str (str): Duration in ISO 8601 format (e.g., 'PT1H2M3S')

        Returns:
            int: Duration in seconds
        """
        import re

        # Extract hours, minutes, seconds using regex
        hours_match = re.search(r"(\d+)H", duration_str)
        minutes_match = re.search(r"(\d+)M", duration_str)
        seconds_match = re.search(r"(\d+)S", duration_str)

        hours = int(hours_match.group(1)) if hours_match else 0
        minutes = int(minutes_match.group(1)) if minutes_match else 0
        seconds = int(seconds_match.group(1)) if seconds_match else 0

        return hours * 3600 + minutes * 60 + seconds

    def _calculate_total_metrics(self, video_stats: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregated metrics for all videos.

        Args:
            video_stats (List[Dict]): List of video statistics

        Returns:
            Dict containing total metrics
        """
        total_views = sum(video.get("view_count", 0) for video in video_stats)
        total_likes = sum(video.get("like_count", 0) for video in video_stats)
        total_comments = sum(video.get("comment_count", 0) for video in video_stats)
        total_duration = sum(video.get("duration_seconds", 0) for video in video_stats)

        # Calculate average engagement rate
        valid_engagement_rates = [
            video.get("engagement_rate", 0)
            for video in video_stats
            if video.get("view_count", 0) > 0
        ]
        avg_engagement_rate = (
            sum(valid_engagement_rates) / len(valid_engagement_rates)
            if valid_engagement_rates
            else 0
        )

        return {
            "total_views": total_views,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": self._format_duration(total_duration),
            "average_engagement_rate": round(avg_engagement_rate, 2),
            "video_count": len(video_stats),
        }

    def _get_top_videos(
        self, video_stats: List[Dict], limit: int = 10
    ) -> Dict[str, List[Dict]]:
        """Get top performing videos by different metrics.

        Args:
            video_stats (List[Dict]): List of video statistics
            limit (int): Number of top videos to return

        Returns:
            Dict containing top videos by different criteria
        """
        # Sort by different metrics
        by_views = sorted(
            video_stats, key=lambda x: x.get("view_count", 0), reverse=True
        )[:limit]
        by_likes = sorted(
            video_stats, key=lambda x: x.get("like_count", 0), reverse=True
        )[:limit]
        by_comments = sorted(
            video_stats, key=lambda x: x.get("comment_count", 0), reverse=True
        )[:limit]
        by_engagement = sorted(
            video_stats, key=lambda x: x.get("engagement_rate", 0), reverse=True
        )[:limit]

        return {
            "by_views": by_views,
            "by_likes": by_likes,
            "by_comments": by_comments,
            "by_engagement": by_engagement,
        }

    def _calculate_engagement_metrics(self, video_stats: List[Dict]) -> Dict[str, Any]:
        """Calculate engagement metrics and distributions.

        Args:
            video_stats (List[Dict]): List of video statistics

        Returns:
            Dict containing engagement analysis
        """
        if not video_stats:
            return {}

        # Calculate engagement rate distribution
        engagement_rates = [video.get("engagement_rate", 0) for video in video_stats]

        # Calculate percentiles
        engagement_rates_sorted = sorted(engagement_rates)
        n = len(engagement_rates_sorted)

        percentiles = {}
        for p in [25, 50, 75, 90, 95]:
            idx = int((p / 100) * (n - 1))
            percentiles[f"p{p}"] = engagement_rates_sorted[idx] if n > 0 else 0

        # Calculate like-to-view ratios
        like_ratios = []
        comment_ratios = []

        for video in video_stats:
            views = video.get("view_count", 0)
            if views > 0:
                like_ratios.append((video.get("like_count", 0) / views) * 100)
                comment_ratios.append((video.get("comment_count", 0) / views) * 100)

        avg_like_ratio = sum(like_ratios) / len(like_ratios) if like_ratios else 0
        avg_comment_ratio = (
            sum(comment_ratios) / len(comment_ratios) if comment_ratios else 0
        )

        return {
            "engagement_percentiles": percentiles,
            "average_like_ratio": round(avg_like_ratio, 3),
            "average_comment_ratio": round(avg_comment_ratio, 3),
            "high_engagement_videos": len(
                [r for r in engagement_rates if r > percentiles.get("p75", 0)]
            ),
            "low_engagement_videos": len(
                [r for r in engagement_rates if r < percentiles.get("p25", 0)]
            ),
        }

    def _calculate_view_distribution(self, video_stats: List[Dict]) -> Dict[str, Any]:
        """Calculate view distribution across videos.

        Args:
            video_stats (List[Dict]): List of video statistics

        Returns:
            Dict containing view distribution data
        """
        if not video_stats:
            return {}

        view_counts = [video.get("view_count", 0) for video in video_stats]
        total_views = sum(view_counts)

        if total_views == 0:
            return {}

        # Calculate distribution percentages
        distribution_data = []
        for video in video_stats:
            views = video.get("view_count", 0)
            percentage = (views / total_views) * 100 if total_views > 0 else 0
            distribution_data.append(
                {
                    "title": video.get("title", ""),
                    "views": views,
                    "percentage": round(percentage, 2),
                    "video_id": video.get("video_id", ""),
                }
            )

        # Sort by views descending
        distribution_data.sort(key=lambda x: x["views"], reverse=True)

        # Calculate concentration metrics
        top_20_percent_count = max(1, len(video_stats) // 5)
        top_20_percent_views = sum(
            video["views"] for video in distribution_data[:top_20_percent_count]
        )
        concentration_ratio = (
            (top_20_percent_views / total_views) * 100 if total_views > 0 else 0
        )

        return {
            "distribution": distribution_data,
            "concentration_ratio": round(concentration_ratio, 2),
            "top_video_share": (
                distribution_data[0]["percentage"] if distribution_data else 0
            ),
        }

    def _get_timeline_data(self, video_stats: List[Dict]) -> Dict[str, Any]:
        """Get timeline-based analytics data.

        Args:
            video_stats (List[Dict]): List of video statistics

        Returns:
            Dict containing timeline analysis
        """
        if not video_stats:
            return {}

        # Filter videos with valid publish dates
        videos_with_dates = [
            video for video in video_stats if video.get("published_at") is not None
        ]

        if not videos_with_dates:
            return {}

        # Sort by publish date
        videos_with_dates.sort(key=lambda x: x["published_at"])

        # Group by month for timeline chart
        monthly_data = {}
        for video in videos_with_dates:
            publish_date = video["published_at"]
            month_key = publish_date.strftime("%Y-%m")

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": publish_date.strftime("%B %Y"),
                    "video_count": 0,
                    "total_views": 0,
                    "total_likes": 0,
                }

            monthly_data[month_key]["video_count"] += 1
            monthly_data[month_key]["total_views"] += video.get("view_count", 0)
            monthly_data[month_key]["total_likes"] += video.get("like_count", 0)

        # Convert to list and sort
        timeline_data = list(monthly_data.values())

        # Calculate performance trends
        if len(timeline_data) > 1:
            recent_period = timeline_data[-3:]  # Last 3 months
            earlier_period = (
                timeline_data[:-3] if len(timeline_data) > 3 else timeline_data[:-1]
            )

            recent_avg_views = sum(
                period["total_views"] for period in recent_period
            ) / len(recent_period)
            earlier_avg_views = sum(
                period["total_views"] for period in earlier_period
            ) / len(earlier_period)

            view_trend = (
                "increasing" if recent_avg_views > earlier_avg_views else "decreasing"
            )
        else:
            view_trend = "stable"

        return {
            "timeline": timeline_data,
            "date_range": {
                "start": videos_with_dates[0]["published_at"].strftime("%Y-%m-%d"),
                "end": videos_with_dates[-1]["published_at"].strftime("%Y-%m-%d"),
            },
            "view_trend": view_trend,
            "most_productive_month": (
                max(timeline_data, key=lambda x: x["video_count"])["month"]
                if timeline_data
                else None
            ),
        }

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human-readable format.

        Args:
            seconds (int): Duration in seconds

        Returns:
            str: Formatted duration string
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        remaining_seconds = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {remaining_seconds}s"
        elif minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"

    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure for error cases.

        Returns:
            Dict with empty analytics structure
        """
        return {
            "total_metrics": {
                "total_views": 0,
                "total_likes": 0,
                "total_comments": 0,
                "total_duration_seconds": 0,
                "total_duration_formatted": "0s",
                "average_engagement_rate": 0,
                "video_count": 0,
            },
            "top_videos": {
                "by_views": [],
                "by_likes": [],
                "by_comments": [],
                "by_engagement": [],
            },
            "engagement_data": {},
            "view_distribution": {},
            "timeline_data": {},
            "raw_video_stats": [],
        }
