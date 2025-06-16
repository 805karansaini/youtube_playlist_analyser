from typing import Literal

from pydantic import Field, PositiveInt, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for YouTube Playlist Analyzer.

    Automatically loads from .env file and provides comprehensive
    application configuration with validation and type safety.

    This class manages configuration settings for the entire application,
    including API keys, logging, caching, security, and performance parameters.

    Attributes:
        YOUTUBE_API_KEY (str): The API key for authenticating with YouTube API.
        YOUTUBE_API_VERSION (str): The version of YouTube API to use (default: "v3").
        MAX_RESULTS (int): Maximum number of results to return per API request (default: 50).
        LOG_LEVEL (str): Application logging level (default: "INFO").
        ENVIRONMENT (str): Environment name (development, staging, production).
        DEBUG (bool): Enable debug mode (default: False).
        PORT (int): Application port number (default: 8090).
        CACHE_TTL (int): Default cache TTL in seconds (default: 3600).
    """

    # Required configuration
    YOUTUBE_API_KEY: str = Field(
        ..., min_length=20, description="YouTube Data API v3 key"
    )

    # YouTube API configuration
    YOUTUBE_API_VERSION: str = Field(default="v3", description="YouTube API version")
    MAX_RESULTS: PositiveInt = Field(
        default=50, le=200, description="Max results per API call"
    )

    # Application configuration
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development", description="Application environment"
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    PORT: PositiveInt = Field(default=8090, le=65535, description="Application port")

    # Performance configuration
    CACHE_TTL: PositiveInt = Field(
        default=3600, description="Cache TTL in seconds"
    )  # 1 hour
    REQUEST_TIMEOUT: PositiveInt = Field(
        default=30, description="Request timeout in seconds"
    )

    # Security configuration
    RATE_LIMIT_PER_MINUTE: PositiveInt = Field(
        default=60, description="Rate limit per minute"
    )
    MAX_PLAYLIST_SIZE: PositiveInt = Field(
        default=1000, description="Maximum playlist size"
    )

    @field_validator("YOUTUBE_API_KEY")
    @classmethod
    def validate_api_key(cls, v):
        """Validate YouTube API key format."""
        if not v or len(v) < 20:
            raise ValueError("YouTube API key must be at least 20 characters")
        return v


    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "forbid"  # Prevent additional fields
