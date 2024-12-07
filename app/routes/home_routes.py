import logging

from core.config import Config
from exceptions.exception import InvalidPlaylistLink
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
    """
    Handle home page requests.

    Returns:
        str: Rendered HTML template for the home page.
    """
    return render_template("home.html")


@bp.route("/", methods=["POST"])
def analyze_playlist() -> str:
    """
    Handle POST requests to analyze YouTube playlist.

    Returns:
        str: Rendered HTML template with playlist analysis results.
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

    except InvalidPlaylistLink as e:
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
