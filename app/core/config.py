from typing import Any, Dict, Literal, Optional

from pydantic import Field, PositiveInt, field_validator, model_validator
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
        STATIC_URL (str): Base URL for the YouTube API playlist items endpoint.
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
    STATIC_URL: str = Field(
        default="https://www.googleapis.com/youtube/v3/playlistItems",
        description="YouTube API base URL",
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

    # Application metadata
    APP_NAME: str = Field(
        default="YouTube Playlist Analyzer", description="Application name"
    )
    APP_VERSION: str = Field(default="2.0.0", description="Application version")
    APP_DESCRIPTION: str = Field(
        default="Advanced YouTube playlist analysis with comprehensive analytics",
        description="Application description",
    )

    # Performance configuration
    CACHE_TTL: PositiveInt = Field(
        default=3600, description="Cache TTL in seconds"
    )  # 1 hour
    REQUEST_TIMEOUT: PositiveInt = Field(
        default=30, description="Request timeout in seconds"
    )
    MAX_RETRIES: PositiveInt = Field(
        default=3, le=10, description="Maximum retry attempts"
    )
    CONNECTION_POOL_SIZE: PositiveInt = Field(
        default=20, description="HTTP connection pool size"
    )

    # Advanced caching configuration
    ENABLE_REDIS_CACHE: bool = Field(default=False, description="Enable Redis caching")
    REDIS_URL: Optional[str] = Field(default=None, description="Redis connection URL")
    CACHE_KEY_PREFIX: str = Field(
        default="youtube_analyzer:", description="Cache key prefix"
    )

    # Security configuration
    RATE_LIMIT_PER_MINUTE: PositiveInt = Field(
        default=60, description="Rate limit per minute"
    )
    MAX_PLAYLIST_SIZE: PositiveInt = Field(
        default=1000, description="Maximum playlist size"
    )
    ALLOWED_ORIGINS: str = Field(default="*", description="CORS allowed origins")
    SECRET_KEY: Optional[str] = Field(
        default=None, description="Application secret key"
    )

    # Database configuration (for future use)
    DATABASE_URL: Optional[str] = Field(
        default=None, description="Database connection URL"
    )
    ENABLE_DATABASE: bool = Field(
        default=False, description="Enable database persistence"
    )

    # Export configuration
    MAX_EXPORT_SIZE_MB: PositiveInt = Field(
        default=100, description="Max export file size in MB"
    )
    EXPORT_FORMATS: str = Field(
        default="csv,json,excel", description="Supported export formats"
    )

    # Analytics configuration
    ENABLE_ENHANCED_ANALYTICS: bool = Field(
        default=True, description="Enable enhanced analytics features"
    )
    ENABLE_VISUAL_ANALYTICS: bool = Field(
        default=True, description="Enable visual analytics charts"
    )
    ANALYTICS_BATCH_SIZE: PositiveInt = Field(
        default=100, description="Batch size for analytics processing"
    )

    @field_validator("YOUTUBE_API_KEY")
    @classmethod
    def validate_api_key(cls, v):
        """Validate YouTube API key format."""
        if not v or len(v) < 20:
            raise ValueError("YouTube API key must be at least 20 characters")
        return v

    @field_validator("SECRET_KEY", mode="before")
    @classmethod
    def generate_secret_key(cls, v):
        """Generate secret key if not provided."""
        if v is None:
            import secrets

            return secrets.token_urlsafe(32)
        return v

    @field_validator("EXPORT_FORMATS")
    @classmethod
    def validate_export_formats(cls, v):
        """Validate export formats."""
        valid_formats = {"csv", "json", "excel", "pdf"}
        formats = set(format.strip().lower() for format in v.split(","))
        invalid = formats - valid_formats
        if invalid:
            raise ValueError(f"Invalid export formats: {invalid}")
        return v

    @model_validator(mode="after")
    def validate_cache_config(self):
        """Validate cache configuration."""
        if self.ENABLE_REDIS_CACHE and not self.REDIS_URL:
            raise ValueError("REDIS_URL is required when ENABLE_REDIS_CACHE is True")
        return self

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT == "staging"

    @property
    def supported_export_formats(self) -> list:
        """Get list of supported export formats."""
        return [fmt.strip().lower() for fmt in self.EXPORT_FORMATS.split(",")]

    @property
    def cache_config(self) -> Dict[str, Any]:
        """Get cache configuration dictionary."""
        return {
            "enabled": True,
            "ttl": self.CACHE_TTL,
            "redis_enabled": self.ENABLE_REDIS_CACHE,
            "redis_url": self.REDIS_URL,
            "key_prefix": self.CACHE_KEY_PREFIX,
        }

    @property
    def performance_config(self) -> Dict[str, Any]:
        """Get performance configuration dictionary."""
        return {
            "request_timeout": self.REQUEST_TIMEOUT,
            "max_retries": self.MAX_RETRIES,
            "connection_pool_size": self.CONNECTION_POOL_SIZE,
            "max_playlist_size": self.MAX_PLAYLIST_SIZE,
            "analytics_batch_size": self.ANALYTICS_BATCH_SIZE,
        }

    @property
    def security_config(self) -> Dict[str, Any]:
        """Get security configuration dictionary."""
        return {
            "rate_limit_per_minute": self.RATE_LIMIT_PER_MINUTE,
            "allowed_origins": self.ALLOWED_ORIGINS,
            "secret_key": self.SECRET_KEY,
            "max_playlist_size": self.MAX_PLAYLIST_SIZE,
        }

    def get_app_info(self) -> Dict[str, str]:
        """Get application information."""
        return {
            "name": self.APP_NAME,
            "version": self.APP_VERSION,
            "description": self.APP_DESCRIPTION,
            "environment": self.ENVIRONMENT,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "forbid"  # Prevent additional fields
