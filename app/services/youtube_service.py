import re
from datetime import timedelta
from typing import Any, Dict, List, Tuple

from core.config import Config
from exceptions.exception import InvalidPlaylistLink
from googleapiclient.discovery import build


class YouTubeService:
    """Handles all YouTube API interactions."""

    def __init__(self, config: Config):
        self.config = config
        self.youtube = build(
            "youtube",
            config.YOUTUBE_API_VERSION,
            developerKey=config.YOUTUBE_API_KEY,
            cache_discovery=False,
        )
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for duration parsing."""
        self.hours_pattern = re.compile(r"(\d+)H")
        self.minutes_pattern = re.compile(r"(\d+)M")
        self.seconds_pattern = re.compile(r"(\d+)S")
        self.playlist_pattern = re.compile(r"^([\S]+list=)?([\w_-]+)[\S]*$")

    def extract_playlist_id(self, playlist_link: str) -> str:
        """Extract playlist ID from URL."""
        match = self.playlist_pattern.match(playlist_link)
        if not match:
            raise InvalidPlaylistLink("Invalid playlist link format")
        return match.group(2)

    def get_playlist_details(
        self, playlist_id: str
    ) -> Tuple[int, float, List[Dict[str, Any]]]:
        """Get complete playlist information."""
        total_seconds = 0
        video_data = []
        next_page_token = ""
        run = 1
        while True:
            try:
                print(f"Run: {run}")
                items = self._get_playlist_page(playlist_id, next_page_token)
                video_info = self._process_videos(items)

                for info in video_info:
                    total_seconds += info["duration_seconds"]
                    video_data.append(
                        {
                            "title": info["title"],
                            "duration_minutes": info["duration_seconds"] / 60,
                        }
                    )

                next_page_token = items.get("nextPageToken")
                if not next_page_token:
                    break
                run += 1
            except Exception as e:
                raise ValueError(f"Error fetching playlist: {str(e)}")

        return len(video_data), total_seconds, video_data

    def _get_playlist_page(self, playlist_id: str, page_token: str) -> Dict:
        """Fetch a single page of playlist items."""
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
        """Process video information from playlist items."""
        video_ids = [
            item["contentDetails"]["videoId"] for item in playlist_items["items"]
        ]

        videos = (
            self.youtube.videos()
            .list(part="contentDetails,snippet", id=",".join(video_ids))
            .execute()
        )

        return [self._extract_video_info(video) for video in videos["items"]]

    def _extract_video_info(self, video: Dict) -> Dict:
        """Extract relevant information from a video item."""
        duration = video["contentDetails"]["duration"]
        seconds = self._parse_duration(duration)

        return {"title": video["snippet"]["title"], "duration_seconds": seconds}

    def _parse_duration(self, duration: str) -> float:
        """Parse ISO 8601 duration to seconds."""
        hours = self.hours_pattern.search(duration)
        minutes = self.minutes_pattern.search(duration)
        seconds = self.seconds_pattern.search(duration)

        return timedelta(
            hours=int(hours.group(1)) if hours else 0,
            minutes=int(minutes.group(1)) if minutes else 0,
            seconds=int(seconds.group(1)) if seconds else 0,
        ).total_seconds()
