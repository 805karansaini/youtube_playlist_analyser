import re
import time
from datetime import timedelta
from functools import lru_cache
from typing import Any, Dict, List, Tuple

from core.config import Config
from core.logging_config import get_logger, log_business_event
from exceptions.exception import (
    InvalidYoutubePlaylistLink,
    YouTubeApiError,
    YouTubeApiQuotaExceeded,
    YouTubeApiResponseError,
)
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class YouTubeService:
    """Service class for handling YouTube API interactions.

    This class provides methods to interact with YouTube API for retrieving and
    processing playlist information, including video durations and details.

    Attributes:
        config (Config): Configuration object containing API settings.
        youtube: YouTube API service object.
    """

    def __init__(self, config: Config):
        """Initialize YouTubeService with enhanced configuration and error handling.

        Args:
            config (Config): Configuration object containing YouTube API settings.

        Raises:
            YouTubeApiError: If initialization fails.
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)

        try:
            # Initialize YouTube API client with enhanced configuration
            self.youtube = build(
                "youtube",
                config.YOUTUBE_API_VERSION,
                developerKey=config.YOUTUBE_API_KEY,
                cache_discovery=False,
            )

            # Compile regex patterns for performance
            self._compile_patterns()

            # Performance tracking
            self._debug_logged = False
            self._request_count = 0
            self._total_quota_used = 0
            self._last_request_time = 0

            # Cache for frequently accessed data
            self._playlist_cache = {}
            self._video_cache = {}

            self.logger.info(
                "YouTubeService initialized successfully",
                extra={
                    "api_version": config.YOUTUBE_API_VERSION,
                    "max_results": config.MAX_RESULTS,
                    "timeout": config.REQUEST_TIMEOUT,
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize YouTubeService: {str(e)}")
            raise YouTubeApiError(f"YouTube service initialization failed: {str(e)}")

    def _compile_patterns(self):
        """Compile regex patterns used for duration parsing.

        Initializes compiled regex patterns for parsing hours, minutes, seconds
        from YouTube duration format, and playlist URL pattern.
        """
        self.hours_pattern = re.compile(r"(\d+)H")
        self.minutes_pattern = re.compile(r"(\d+)M")
        self.seconds_pattern = re.compile(r"(\d+)S")
        self.playlist_pattern = re.compile(r"^([\S]+list=)?([\w_-]+)[\S]*$")

    def extract_playlist_id(self, playlist_link: str) -> str:
        """Extract playlist ID from a YouTube playlist URL.

        Args:
            playlist_link (str): Full YouTube playlist URL or just the playlist ID.

        Returns:
            str: The extracted playlist ID.

        Raises:
            InvalidYoutubePlaylistLink: If the provided URL is not a valid YouTube playlist link.
        """
        match = self.playlist_pattern.match(playlist_link)
        if not match:
            raise InvalidYoutubePlaylistLink(
                "The provided URL is not a valid YouTube playlist link"
            )
        return match.group(2)

    def get_playlist_details(
        self, playlist_id: str
    ) -> Tuple[int, float, List[Dict[str, Any]]]:
        """Retrieve complete information about a YouTube playlist with enhanced error handling.

        Args:
            playlist_id (str): YouTube playlist ID.

        Returns:
            Tuple containing:
                - int: Total number of videos in playlist
                - float: Total duration in seconds
                - List[Dict[str, Any]]: List of video details containing comprehensive metadata

        Raises:
            YouTubeApiError: If there's an error fetching the playlist information.
            YouTubeApiQuotaExceeded: If API quota is exceeded.
            YouTubeApiResponseError: If API returns an error response.
        """
        if not playlist_id or not playlist_id.strip():
            raise YouTubeApiError("Playlist ID cannot be empty")

        # Check cache first
        cache_key = f"playlist_{playlist_id}"
        if cache_key in self._playlist_cache:
            cached_data = self._playlist_cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.config.CACHE_TTL:
                self.logger.info(f"Returning cached data for playlist {playlist_id}")
                return cached_data["data"]

        start_time = time.time()
        total_seconds = 0
        video_data = []
        next_page_token = ""
        page_count = 0

        log_business_event(
            event_type="playlist_analysis_started", playlist_id=playlist_id
        )

        try:
            while True:
                page_count += 1

                # Rate limiting check
                self._check_rate_limit()

                try:
                    items = self._get_playlist_page(playlist_id, next_page_token)
                    self._request_count += 1
                    self._total_quota_used += 1  # Approximate quota usage

                    if not items.get("items"):
                        self.logger.warning(
                            f"No items found for playlist {playlist_id} on page {page_count}"
                        )
                        break

                    video_info = self._process_videos(items)

                    for info in video_info:
                        total_seconds += info["duration_seconds"]
                        video_data.append(info)

                    next_page_token = items.get("nextPageToken")
                    if not next_page_token:
                        break

                    # Safety check for infinite loops
                    if page_count > 100:  # Reasonable limit
                        self.logger.warning(
                            f"Too many pages ({page_count}) for playlist {playlist_id}"
                        )
                        break

                except HttpError as e:
                    self._handle_api_error(e, playlist_id)

                except Exception as e:
                    self.logger.error(
                        f"Unexpected error processing playlist page: {str(e)}"
                    )
                    raise YouTubeApiError(f"Error processing playlist data: {str(e)}")

            # Validate results
            if not video_data:
                raise YouTubeApiError(f"No videos found in playlist {playlist_id}")

            if len(video_data) > self.config.MAX_PLAYLIST_SIZE:
                self.logger.warning(
                    f"Playlist {playlist_id} exceeds maximum size limit ({len(video_data)} > {self.config.MAX_PLAYLIST_SIZE})"
                )

            result = (len(video_data), total_seconds, video_data)

            # Cache the result
            self._playlist_cache[cache_key] = {"data": result, "timestamp": time.time()}

            # Log success metrics
            processing_time = time.time() - start_time
            log_business_event(
                event_type="playlist_analysis_completed",
                playlist_id=playlist_id,
                video_count=len(video_data),
                total_duration=total_seconds,
                processing_time=processing_time,
                pages_processed=page_count,
            )

            self.logger.info(
                f"Successfully processed playlist {playlist_id}",
                extra={
                    "video_count": len(video_data),
                    "total_duration_seconds": total_seconds,
                    "processing_time": processing_time,
                    "pages_processed": page_count,
                    "quota_used": self._total_quota_used,
                },
            )

            return result

        except YouTubeApiError:
            # Re-raise YouTube API errors
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error fetching playlist {playlist_id}: {str(e)}"
            )
            raise YouTubeApiError(f"Error fetching playlist: {str(e)}")

    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        current_time = time.time()
        if self._last_request_time > 0:
            time_diff = current_time - self._last_request_time
            min_interval = 60.0 / self.config.RATE_LIMIT_PER_MINUTE

            if time_diff < min_interval:
                sleep_time = min_interval - time_diff
                self.logger.debug(
                    f"Rate limiting: sleeping for {sleep_time:.2f} seconds"
                )
                time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _handle_api_error(self, error: HttpError, context: str = "") -> None:
        """Handle YouTube API errors with specific error types.

        Args:
            error: The HTTP error from the API.
            context: Additional context about where the error occurred.

        Raises:
            YouTubeApiQuotaExceeded: If quota is exceeded.
            YouTubeApiResponseError: For other API errors.
        """
        error_details = error.error_details if hasattr(error, "error_details") else []
        status_code = error.resp.status if hasattr(error, "resp") else None

        self.logger.error(
            f"YouTube API error in {context}",
            extra={
                "status_code": status_code,
                "error_details": error_details,
                "context": context,
            },
        )

        # Check for quota exceeded
        if status_code == 403:
            for detail in error_details:
                if detail.get("reason") == "quotaExceeded":
                    raise YouTubeApiQuotaExceeded("YouTube API quota exceeded")

        # Handle other specific errors
        error_message = str(error)
        if "quotaExceeded" in error_message:
            raise YouTubeApiQuotaExceeded("YouTube API quota exceeded")
        elif "playlistNotFound" in error_message or status_code == 404:
            raise YouTubeApiResponseError(
                "Playlist not found", status_code, error_details
            )
        elif status_code == 400:
            raise YouTubeApiResponseError(
                "Invalid request parameters", status_code, error_details
            )
        else:
            raise YouTubeApiResponseError(
                f"YouTube API error: {error_message}", status_code, error_details
            )

    def _get_playlist_page(self, playlist_id: str, page_token: str) -> Dict:
        """Fetch a single page of playlist items from YouTube API.

        Args:
            playlist_id (str): YouTube playlist ID.
            page_token (str): Token for pagination, empty for first page.

        Returns:
            Dict: Raw API response containing playlist items information.
        """
        return (
            self.youtube.playlistItems()
            .list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=self.config.MAX_RESULTS,
                pageToken=page_token,
            )
            .execute()
        )

    def _process_videos(self, playlist_items: Dict) -> List[Dict]:
        """Process video information from playlist items.

        Args:
            playlist_items (Dict): Raw playlist items from YouTube API.

        Returns:
            List[Dict]: List of processed video information containing title and duration.
        """
        video_ids = [
            item["contentDetails"]["videoId"] for item in playlist_items["items"]
        ]

        videos = (
            self.youtube.videos()
            .list(part="contentDetails,snippet,statistics", id=",".join(video_ids))
            .execute()
        )

        return [self._extract_video_info(video) for video in videos["items"]]

    def _extract_video_info(self, video: Dict) -> Dict:
        """Extract relevant information from a video item.

        Args:
            video (Dict): Raw video information from YouTube API.

        Returns:
            Dict: Processed video information containing comprehensive metadata
        """
        duration = video["contentDetails"]["duration"]
        seconds = self._parse_duration(duration)

        snippet = video.get("snippet", {})
        statistics = video.get("statistics", {})

        # Debug logging for first video
        if not self._debug_logged:
            # Mark that we've logged the debug information once
            self._debug_logged = True
            self.logger.info(f"YouTube API video data keys: {list(video.keys())}")
            self.logger.info(f"Statistics data: {statistics}")
            self.logger.info(f"Snippet data keys: {list(snippet.keys())}")

        # Handle missing statistics gracefully
        try:
            view_count = int(statistics.get("viewCount", "0") or "0")
            like_count = int(statistics.get("likeCount", "0") or "0")
            comment_count = int(statistics.get("commentCount", "0") or "0")
        except (ValueError, TypeError):
            view_count = like_count = comment_count = 0

        return {
            "video_id": video.get("id", ""),
            "title": snippet.get("title", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "description": (
                snippet.get("description", "")[:500]
                if snippet.get("description")
                else ""
            ),
            "published_at": snippet.get("publishedAt", ""),
            "duration_seconds": seconds,
            "duration_minutes": seconds / 60,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "thumbnail_url": snippet.get("thumbnails", {})
            .get("medium", {})
            .get("url", ""),
        }

    def _parse_duration(self, duration: str) -> float:
        """Parse ISO 8601 duration format to seconds.

        Args:
            duration (str): Duration string in ISO 8601 format (e.g., 'PT1H2M10S').

        Returns:
            float: Duration in seconds.
        """
        hours = self.hours_pattern.search(duration)
        minutes = self.minutes_pattern.search(duration)
        seconds = self.seconds_pattern.search(duration)

        return timedelta(
            hours=int(hours.group(1)) if hours else 0,
            minutes=int(minutes.group(1)) if minutes else 0,
            seconds=int(seconds.group(1)) if seconds else 0,
        ).total_seconds()



    def get_service_statistics(self) -> Dict[str, Any]:
        """Get service usage statistics.

        Returns:
            Dictionary containing service statistics.
        """
        return {
            "requests_made": self._request_count,
            "quota_used_estimate": self._total_quota_used,
            "cache_size": len(self._playlist_cache) + len(self._video_cache),
            "playlist_cache_hits": len(self._playlist_cache),
            "video_cache_hits": len(self._video_cache),
        }

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._playlist_cache.clear()
        self._video_cache.clear()
        self.logger.info("Service cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached data.

        Returns:
            Dictionary containing cache information.
        """
        current_time = time.time()

        playlist_cache_info = []
        for key, data in self._playlist_cache.items():
            age = current_time - data["timestamp"]
            playlist_cache_info.append(
                {"key": key, "age_seconds": age, "expired": age > self.config.CACHE_TTL}
            )

        return {
            "playlist_cache_entries": len(self._playlist_cache),
            "video_cache_entries": len(self._video_cache),
            "cache_ttl": self.config.CACHE_TTL,
            "playlist_cache_details": playlist_cache_info,
        }
