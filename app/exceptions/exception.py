"""Exceptions for the YouTube Playlist Analyzer.

This module defines custom exceptions for the YouTube Playlist Analyzer application.
"""


class YouTubeApiError(Exception):
    """Base exception for YouTube API errors.

    This is the base class for all YouTube API related exceptions.

    Args:
        message (str, optional): Explanation of the error. Defaults to None.
    """

    def __init__(self, message=None):
        """Initialize the YouTubeApiError exception.

        Args:
            message (str, optional): Custom error message. Defaults to None.
        """
        super().__init__(message)


class InvalidYoutubePlaylistLink(YouTubeApiError):
    """Exception raised when playlist link is not valid.

    This exception is raised when the provided YouTube playlist link is incorrect,
    inaccessible, or does not follow the expected format.

    Args:
        message (str, optional): Explanation of the error. Defaults to None.

    Raises:
        InvalidYoutubePlaylistLink: When the playlist URL is not valid.

    Example:
        >>> raise InvalidYoutubePlaylistLink("The provided URL is not a valid YouTube playlist link")
    """

    def __init__(self, message=None):
        """Initialize the InvalidYoutubePlaylistLink exception.

        Args:
            message (str, optional): Custom error message explaining why the playlist link is invalid.
                Defaults to None.
        """
        super().__init__(message)


class YouTubeApiQuotaExceeded(YouTubeApiError):
    """Exception raised when YouTube API quota is exceeded.

    This exception is raised when the YouTube API quota has been exceeded.

    Args:
        message (str, optional): Explanation of the error. Defaults to None.
    """

    def __init__(self, message=None):
        """Initialize the YouTubeApiQuotaExceeded exception.

        Args:
            message (str, optional): Custom error message. Defaults to None.
        """
        super().__init__(message or "YouTube API quota exceeded")


class YouTubeApiResponseError(YouTubeApiError):
    """Exception raised when YouTube API returns an error response.

    This exception is raised when the YouTube API returns an error response.

    Args:
        message (str, optional): Explanation of the error. Defaults to None.
        status_code (int, optional): HTTP status code. Defaults to None.
        error_details (dict, optional): Additional error details. Defaults to None.
    """

    def __init__(self, message=None, status_code=None, error_details=None):
        """Initialize the YouTubeApiResponseError exception.

        Args:
            message (str, optional): Custom error message. Defaults to None.
            status_code (int, optional): HTTP status code. Defaults to None.
            error_details (dict, optional): Additional error details. Defaults to None.
        """
        self.status_code = status_code
        self.error_details = error_details or {}
        super().__init__(message or "YouTube API returned an error response")


class PlaylistAnalysisError(Exception):
    """Exception raised when there's an error analyzing a playlist.

    This exception is raised when there's an error analyzing a playlist.

    Args:
        message (str, optional): Explanation of the error. Defaults to None.
        cause (Exception, optional): The underlying exception that caused this error. Defaults to None.
    """

    def __init__(self, message=None, cause=None):
        """Initialize the PlaylistAnalysisError exception.

        Args:
            message (str, optional): Custom error message. Defaults to None.
            cause (Exception, optional): The underlying exception that caused this error. Defaults to None.
        """
        self.cause = cause
        super().__init__(message or "Error analyzing playlist")
