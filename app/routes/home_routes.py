import logging

from core.config import Config
from exceptions.exception import InvalidYoutubePlaylistLink
from flask import Blueprint, render_template, request
from helper.utils import format_duration
from services.youtube_service import YouTubeService

bp = Blueprint("home", __name__)
logger = logging.getLogger(__name__)

# Initialize YouTube service
config = Config()  # type: ignore
youtube_service = YouTubeService(config)


@bp.route("/", methods=["GET"])
def home() -> str:
    """This route function serves the home page of the application by rendering
    the 'home.html' template.

    Returns:
        str: The rendered HTML content of the home page.

    Example:
        When accessing the root URL ('/'), this function will be called and
        return the rendered home page template.
    """
    return render_template("home.html")


@bp.route("/", methods=["POST"])
def analyze_playlist() -> str:
    """
    This function processes a YouTube playlist URL submitted via POST request,
    extracts playlist information, and returns analyzed data including video count,
    durations, and playback speed calculations.

    Returns:
        str: Rendered HTML template containing:
            - Playlist statistics (video count, average length, total duration)
            - Playback duration at different speeds (1.25x - 2.00x)
            - Chart data with video titles and durations

    Raises:
        InvalidYoutubePlaylistLink: If the provided playlist URL is invalid or malformed
        Exception: For any other unexpected errors during processing

    Example usage:
        POST / with form data containing:
        {
            "search_string": "https://www.youtube.com/playlist?list=PLAYLIST_ID"
        }
    """
    try:
        user_link = request.form.get("search_string", "").strip()
        playlist_id = youtube_service.extract_playlist_id(user_link)
        video_count, total_seconds, videos = youtube_service.get_playlist_details(
            playlist_id
        )

        # Prepare chart data
        chart_data = [
            [video["title"] for video in videos],
            [video["duration_minutes"] for video in videos],
        ]

        # Prepare display text
        display_text = [
            f"No of videos: {video_count}",
            f"Average length of a video: {format_duration(total_seconds/video_count)}",
            f"Total length of playlist: {format_duration(total_seconds)}",
            f"At 1.25x: {format_duration(total_seconds/1.25)}",
            f"At 1.50x: {format_duration(total_seconds/1.50)}",
            f"At 1.75x: {format_duration(total_seconds/1.75)}",
            f"At 2.00x: {format_duration(total_seconds/2.00)}",
        ]

        return render_template(
            "home.html", display_text=display_text, chart_data=chart_data
        )

    except InvalidYoutubePlaylistLink as e:
        logger.error(f"Invalid playlist error: {str(e)}")
        return render_template(
            "home.html",
            display_text=[
                "Invalid playlist link",
                "Please try again with correct parameters",
            ],
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template(
            "home.html",
            display_text=["An unexpected error occurred", "Please try again later"],
        )
