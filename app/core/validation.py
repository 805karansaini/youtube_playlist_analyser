"""Input validation schemas and utilities for the YouTube Playlist Analyzer.

This module provides Pydantic models for validating user inputs and API requests,
ensuring data integrity and security throughout the application.
"""

import re
from typing import Any, Dict, List, Optional, Type
from urllib.parse import parse_qs, urlparse
from datetime import datetime, timezone

from pydantic import BaseModel, Field, field_validator


class PlaylistUrlRequest(BaseModel):
    """Request model for playlist URL validation.

    Validates YouTube playlist URLs and extracts playlist IDs.
    """

    url: str = Field(
        ..., description="YouTube playlist URL", min_length=10, max_length=500
    )

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """Validate and sanitize YouTube playlist URL.

        Args:
            v: The URL string to validate

        Returns:
            Validated URL string

        Raises:
            ValueError: If URL is not a valid YouTube playlist URL
        """
        # Remove extra whitespace and normalize
        url = v.strip()

        # Check if URL is from YouTube domain
        try:
            parsed = urlparse(url)
            if parsed.netloc.lower() not in [
                "www.youtube.com",
                "youtube.com",
                "m.youtube.com",
            ]:
                raise ValueError("URL must be from YouTube")
        except Exception:
            raise ValueError("Invalid URL format")

        # Extract playlist ID
        playlist_id = cls.extract_playlist_id(url)
        if not playlist_id:
            raise ValueError("URL must contain a valid playlist ID")

        return url

    @staticmethod
    def extract_playlist_id(url: str) -> Optional[str]:
        """Extract playlist ID from YouTube URL.

        Args:
            url: YouTube playlist URL

        Returns:
            Playlist ID if found, None otherwise
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            # Check for playlist parameter
            if "list" in query_params:
                playlist_id = query_params["list"][0]
                # A valid playlist ID is at least 12 characters (video IDs are 11) and contains only permitted chars
                if re.match(r"^[a-zA-Z0-9_-]{12,}$", playlist_id):
                    return playlist_id

        except Exception:
            pass

        return None

    def get_playlist_id(self) -> Optional[str]:
        """Get the playlist ID from the validated URL.

        Returns:
            Playlist ID extracted from the URL
        """
        return self.extract_playlist_id(self.url)


class PlaylistAnalysisRequest(BaseModel):
    """Request model for playlist analysis parameters."""

    playlist_url: str = Field(..., description="YouTube playlist URL to analyze")

    analysis_type: str = Field(
        default="basic",
        description="Type of analysis to perform",
        pattern="^(basic|detailed|trends|sentiment)$",
    )

    max_videos: Optional[int] = Field(
        default=None, description="Maximum number of videos to analyze", ge=1, le=1000
    )

    include_metadata: bool = Field(
        default=True, description="Include video metadata in analysis"
    )

    @field_validator("playlist_url")
    @classmethod
    def validate_playlist_url(cls, v: str) -> str:
        """Validate playlist URL using PlaylistUrlRequest."""
        url_request = PlaylistUrlRequest(url=v)
        return url_request.url


class VideoMetadata(BaseModel):
    """Model for video metadata validation."""

    video_id: str = Field(..., min_length=11, max_length=11)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    duration: Optional[str] = Field(default=None)
    view_count: Optional[int] = Field(default=None, ge=0)
    like_count: Optional[int] = Field(default=None, ge=0)
    published_at: Optional[str] = Field(default=None)
    channel_title: Optional[str] = Field(default=None, max_length=100)

    @field_validator("video_id")
    @classmethod
    def validate_video_id(cls, v: str) -> str:
        """Validate YouTube video ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]{11}$", v):
            raise ValueError("Invalid YouTube video ID format")
        return v

    @field_validator("title", "description", "channel_title")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS and injection attacks."""
        if v is None:
            return v

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'\&]', "", v.strip())
        return sanitized if sanitized else None


class PlaylistMetadata(BaseModel):
    """Model for playlist metadata validation."""

    playlist_id: str = Field(..., min_length=12, max_length=50)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    channel_title: Optional[str] = Field(default=None, max_length=100)
    video_count: int = Field(..., ge=0, le=10000)
    videos: List[VideoMetadata] = Field(default_factory=list)

    @field_validator("playlist_id")
    @classmethod
    def validate_playlist_id(cls, v: str) -> str:
        """Validate YouTube playlist ID format."""
        # Accept any playlist ID that has at least 12 characters (video IDs are 11)
        if not re.match(r"^[a-zA-Z0-9_-]{12,}$", v):
            raise ValueError("Invalid YouTube playlist ID format")
        return v

    @field_validator("title", "description", "channel_title")
    @classmethod
    def sanitize_text_fields(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize text fields to prevent XSS and injection attacks."""
        if v is None:
            return v

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'\&]', "", v.strip())
        return sanitized if sanitized else None


class AnalysisResult(BaseModel):
    """Model for analysis result validation."""

    playlist_id: str
    analysis_type: str
    video_count: int = Field(ge=0)
    total_duration: Optional[str] = None
    average_duration: Optional[str] = None
    total_views: Optional[int] = Field(default=None, ge=0)
    total_likes: Optional[int] = Field(default=None, ge=0)
    top_videos: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = Field(default=None, max_length=1000)

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
        extra = "forbid"  # Forbid extra fields


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(
        default=None, description="Request ID for tracking"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional error details"
    )

    class Config:
        """Pydantic configuration."""

        extra = "forbid"


def validate_request_data(
    data: Dict[str, Any], model_class: Type[BaseModel]
) -> BaseModel:
    """Validate request data against a Pydantic model.

    Args:
        data: Request data to validate
        model_class: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        ValueError: If validation fails
    """
    try:
        return model_class(**data)
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem operations
    """
    # Remove directory separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", filename.strip())

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip(". ")

    # Ensure filename isn't empty
    if not sanitized:
        sanitized = "untitled"

    # Limit length
    return sanitized[:255]


# Request Models for Home Routes
class HomePageRequest(BaseModel):
    """Request model for home page form submission."""

    search_string: str = Field(
        ...,
        description="YouTube playlist URL from form input",
        min_length=10,
        max_length=500,
        alias="search_string",
    )

    @field_validator("search_string")
    @classmethod
    def validate_playlist_url(cls, v: str) -> str:
        """Validate playlist URL using PlaylistUrlRequest."""
        url_request = PlaylistUrlRequest(url=v)
        return url_request.url


# Enhanced Export Request Models
class ExportRequest(BaseModel):
    """Base request model for export operations."""

    playlist_url: str = Field(
        ..., description="YouTube playlist URL", min_length=10, max_length=500
    )
    analysis_type: str = Field(
        default="basic",
        description="Type of analysis to perform",
        pattern="^(basic|detailed|trends|sentiment)$",
    )

    @field_validator("playlist_url")
    @classmethod
    def validate_playlist_url(cls, v: str) -> str:
        """Validate playlist URL using PlaylistUrlRequest."""
        url_request = PlaylistUrlRequest(url=v)
        return url_request.url


class JsonExportRequest(ExportRequest):
    """Request model for JSON export with pretty printing option."""

    pretty: bool = Field(
        default=True, description="Enable pretty printing for JSON output"
    )


# Response Models
class SuccessResponse(BaseModel):
    """Standard success response model."""

    success: bool = Field(default=True, description="Operation success status")
    message: Optional[str] = Field(default=None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")

    class Config:
        extra = "allow"


class ChartDataResponse(BaseModel):
    """Response model for chart data endpoint."""

    success: bool = Field(default=True)
    playlist_id: str = Field(..., description="YouTube playlist ID")
    chart_data: Dict[str, Any] = Field(..., description="Chart visualization data")
    metadata: Dict[str, Any] = Field(..., description="Analysis metadata")

    class Config:
        extra = "forbid"


class ExportFormatsResponse(BaseModel):
    """Response model for available export formats."""

    success: bool = Field(default=True)
    formats: Dict[str, Dict[str, str]] = Field(
        ..., description="Available export formats"
    )
    chart_data_endpoint: str = Field(..., description="Chart data API endpoint")

    class Config:
        extra = "forbid"


class PlaylistAnalysisResponse(BaseModel):
    """Response model for playlist analysis results."""

    playlist_id: str = Field(..., description="YouTube playlist ID")
    title: Optional[str] = Field(default=None, description="Playlist title")
    channel_title: Optional[str] = Field(default=None, description="Channel name")
    video_count: int = Field(..., ge=0, description="Number of videos")
    total_duration: str = Field(..., description="Total playlist duration")
    average_duration: str = Field(..., description="Average video duration")
    total_views: Optional[int] = Field(
        default=None, ge=0, description="Total view count"
    )
    total_likes: Optional[int] = Field(
        default=None, ge=0, description="Total like count"
    )
    playback_speeds: Dict[str, str] = Field(
        ..., description="Durations at different speeds"
    )
    top_videos: List[Dict[str, Any]] = Field(
        default_factory=list, description="Top performing videos"
    )
    chart_data: Dict[str, Any] = Field(
        default_factory=dict, description="Chart visualization data"
    )
    analysis_type: str = Field(
        default="basic", description="Type of analysis performed"
    )
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    class Config:
        extra = "forbid"


def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL.

    Args:
        url: YouTube video URL

    Returns:
        Video ID if found, None otherwise
    """
    try:
        parsed = urlparse(url)

        # Handle different YouTube URL formats
        if parsed.netloc in ["www.youtube.com", "youtube.com", "m.youtube.com"]:
            if "watch" in parsed.path:
                query_params = parse_qs(parsed.query)
                if "v" in query_params:
                    video_id = query_params["v"][0]
            elif "/embed/" in parsed.path:
                video_id = parsed.path.split("/embed/")[-1].split("?")[0]
            else:
                return None
        elif parsed.netloc == "youtu.be":
            video_id = parsed.path.lstrip("/")
        else:
            return None

        # Validate video ID format
        if re.match(r"^[a-zA-Z0-9_-]{11}$", video_id):
            return video_id

    except Exception:
        pass

    return None
