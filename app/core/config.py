from typing import Literal

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Application configuration using Pydantic.
    Automatically reads configuration from .env file.
    """

    YOUTUBE_API_KEY: str

    # Optional configuration with defaults
    YOUTUBE_API_VERSION: Literal["v3"] = "v3"
    MAX_RESULTS: int = 50  # Maximum number of results per page
    STATIC_URL: str = "https://www.googleapis.com/youtube/v3/playlistItems"
