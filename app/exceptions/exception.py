class InvalidYoutubePlaylistLink(Exception):
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

    pass
