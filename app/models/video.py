"""Video Model.

This module provides model classes for representing videos with enhanced validation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Video(BaseModel):
    """Model class for representing a video with comprehensive metadata.

    This class represents a video with its comprehensive metadata including
    engagement metrics, publishing information, and duration details.

    Attributes:
        video_id: The unique ID of the video.
        title: The title of the video.
        channel_title: The name of the channel that published the video.
        description: The video description (truncated).
        published_at: The publication date and time.
        duration_seconds: The duration of the video in seconds.
        view_count: The total number of views.
        like_count: The total number of likes.
        comment_count: The total number of comments.
        thumbnail_url: URL to the video thumbnail.
    """

    video_id: str = Field(..., min_length=1, description="YouTube video ID")
    title: str = Field(..., min_length=1, description="Video title")
    channel_title: str = Field(default="", description="Channel name")
    description: str = Field(default="", description="Video description")
    published_at: Optional[str] = Field(
        default=None, description="Publication timestamp"
    )
    duration_seconds: float = Field(ge=0, description="Duration in seconds")
    view_count: int = Field(ge=0, default=0, description="Total views")
    like_count: int = Field(ge=0, default=0, description="Total likes")
    comment_count: int = Field(ge=0, default=0, description="Total comments")
    thumbnail_url: str = Field(default="", description="Thumbnail URL")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
        extra = "forbid"

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        """Validate that duration is reasonable."""
        if v < 0:
            raise ValueError("Duration cannot be negative")

        # Maximum reasonable duration is now 30 days
        if v > 30 * 24 * 3600:  # More than 30 days seems unreasonable
            raise ValueError("Duration seems too long (>30 days)")
        return v

    @property
    def duration_minutes(self) -> float:
        """Get the duration of the video in minutes.

        Returns:
            The duration of the video in minutes.
        """
        return self.duration_seconds / 60

    @property
    def formatted_duration(self) -> str:
        """Get the formatted duration of the video.

        Returns:
            The formatted duration of the video.
        """
        from helper.utils import format_duration

        return format_duration(self.duration_seconds)

    @property
    def engagement_rate(self) -> float:
        """Calculate engagement rate as likes per view.

        Returns:
            Engagement rate as a percentage.
        """
        if self.view_count == 0:
            return 0.0
        return (self.like_count / self.view_count) * 100

    @property
    def published_date(self) -> Optional[datetime]:
        """Parse and return the published date.

        Returns:
            Parsed datetime object or None if invalid.
        """
        if not self.published_at:
            return None
        try:
            return datetime.fromisoformat(self.published_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return None
