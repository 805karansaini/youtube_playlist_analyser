from pydantic import PositiveInt
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for YouTube API integration. Automatically loads from .env file.

    This class manages configuration settings for interacting with the YouTube API,
    including API keys, version information, and request parameters.

    Attributes:
        YOUTUBE_API_KEY (str): The API key for authenticating with YouTube API.
        YOUTUBE_API_VERSION (str): The version of YouTube API to use (default: "v3").
        MAX_RESULTS (int): Maximum number of results to return per API request (default: 50).
        STATIC_URL (str): Base URL for the YouTube API playlist items endpoint.
    """

    YOUTUBE_API_KEY: str

    # Optional configuration with defaults
    YOUTUBE_API_VERSION: str = "v3"
    MAX_RESULTS: PositiveInt = 50
    STATIC_URL: str = "https://www.googleapis.com/youtube/v3/playlistItems"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
