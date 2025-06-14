"""Home Routes.

This module defines the routes for the home page of the application.
"""

import logging

from core.validation import HomePageRequest, validate_request_data
from exceptions.exception import PlaylistAnalysisError, YouTubeApiError
from flask import Blueprint, current_app, jsonify, render_template, request
from pydantic import ValidationError

bp = Blueprint("home", __name__)
logger = logging.getLogger(__name__)


@bp.route("/", methods=["GET"])
def home() -> str:
    """Serve the home page.

    This route function serves the home page of the application by rendering
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
    """Process a YouTube playlist URL and return analysis.

    This function processes a YouTube playlist URL submitted via POST request,
    extracts playlist information, and returns analyzed data including video count,
    durations, and playback speed calculations.

    Returns:
        str: Rendered HTML template containing:
            - Playlist statistics (video count, average length, total duration)
            - Playback duration at different speeds (1.25x - 2.00x)
            - Chart data with video titles and durations

    Raises:
        YouTubeApiError: If there's an error with the YouTube API
        PlaylistAnalysisError: If there's an error analyzing the playlist

    Example usage:
        POST / with form data containing:
        {
            "search_string": "https://www.youtube.com/playlist?list=PLAYLIST_ID"
        }
    """
    try:
        # Validate form data using Pydantic
        form_data = request.form.to_dict()
        if not form_data.get("search_string"):
            return render_template(
                "home.html",
                display_text=[
                    "Please provide a YouTube playlist URL",
                    "Make sure the URL is valid",
                ],
            )

        try:
            validated_request = validate_request_data(form_data, HomePageRequest)
            user_link = validated_request.search_string
        except ValidationError as e:
            logger.warning(f"Form validation error: {str(e)}")
            return render_template(
                "home.html",
                display_text=[
                    "Invalid playlist URL format",
                    "Please check your URL and try again",
                ],
            )
        except ValueError as e:
            logger.warning(f"Form validation error: {str(e)}")
            return render_template(
                "home.html",
                display_text=[
                    "Invalid playlist URL",
                    "Please check your URL and try again",
                ],
            )

        # Get service from container
        analyzer_service = current_app.container.get_playlist_analyzer_service()

        # Create and execute command using Command pattern
        from commands.command import AnalyzePlaylistCommand, CommandInvoker

        command = AnalyzePlaylistCommand(analyzer_service, user_link)
        invoker = CommandInvoker()
        result = invoker.execute_command(command)

        # Store the playlist URL in session or pass it to template
        return render_template(
            "home.html",
            display_text=result["display_text"],
            chart_data=result["chart_data"],
            analysis_data=result.get("analysis_data"),
            visual_analytics=result.get("visual_analytics"),
            playlist_url=user_link,
        )

    except YouTubeApiError as e:
        logger.error(f"YouTube API error: {str(e)}")
        return render_template(
            "home.html",
            display_text=[
                "Invalid playlist link",
                "Please try again with correct parameters",
            ],
        )
    except PlaylistAnalysisError as e:
        logger.error(f"Playlist analysis error: {str(e)}")
        return render_template(
            "home.html",
            display_text=[
                "Error analyzing playlist",
                "Please try again later",
            ],
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return render_template(
            "home.html",
            display_text=["An unexpected error occurred", "Please try again later"],
        )


@bp.route("/api/chart-data", methods=["POST"])
def get_chart_data():
    """Get enhanced visual analytics chart data for a playlist.

    This API endpoint processes a YouTube playlist URL and returns comprehensive
    visual analytics data for rendering interactive charts including top videos,
    engagement metrics, view distribution, and timeline analysis.

    Returns:
        JSON response containing:
            - chart_data: Structured data for Chart.js visualization
            - success: Boolean indicating operation success
            - error: Error message if operation failed

    Example:
        POST /api/chart-data with JSON body:
        {
            "playlist_url": "https://www.youtube.com/playlist?list=PLAYLIST_ID"
        }
    """
    try:
        # Get playlist URL from request
        request_data = request.get_json()
        if not request_data or not request_data.get("playlist_url"):
            return jsonify({"success": False, "error": "Playlist URL is required"}), 400

        playlist_url = request_data.get("playlist_url")

        # Get analyzer service
        analyzer_service = current_app.container.get_playlist_analyzer_service()

        # Analyze playlist
        from commands.command import AnalyzePlaylistCommand, CommandInvoker

        command = AnalyzePlaylistCommand(analyzer_service, playlist_url)
        invoker = CommandInvoker()
        result = invoker.execute_command(command)

        # Get visual analytics data
        visual_analytics = result.get("visual_analytics", {})

        if not visual_analytics:
            # If no visual analytics, provide basic chart data
            return jsonify(
                {
                    "success": True,
                    "chart_data": {
                        "video_performance": {
                            "type": "bar",
                            "data": {
                                "labels": result.get("chart_data", [[], []])[0],
                                "datasets": [
                                    {
                                        "label": "Duration (minutes)",
                                        "data": result.get("chart_data", [[], []])[1],
                                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                                        "borderColor": "rgba(54, 162, 235, 1)",
                                        "borderWidth": 1,
                                    }
                                ],
                            },
                            "title": "Video Duration Analysis",
                        }
                    },
                }
            )

        # Transform visual analytics to Chart.js format
        chart_data = {
            "video_performance": {
                "type": visual_analytics.get("top_videos", {})
                .get("by_views", {})
                .get("type", "bar"),
                "data": {
                    "labels": visual_analytics.get("top_videos", {})
                    .get("by_views", {})
                    .get("labels", []),
                    "datasets": [
                        {
                            "label": "Views",
                            "data": visual_analytics.get("top_videos", {})
                            .get("by_views", {})
                            .get("data", []),
                            "backgroundColor": "rgba(54, 162, 235, 0.2)",
                            "borderColor": "rgba(54, 162, 235, 1)",
                            "borderWidth": 1,
                        }
                    ],
                },
                "title": visual_analytics.get("top_videos", {})
                .get("by_views", {})
                .get("title", "Top Videos by Views"),
            },
            "engagement_metrics": {
                "type": visual_analytics.get("engagement", {})
                .get("overview", {})
                .get("type", "doughnut"),
                "data": {
                    "labels": visual_analytics.get("engagement", {})
                    .get("overview", {})
                    .get("labels", []),
                    "datasets": [
                        {
                            "data": visual_analytics.get("engagement", {})
                            .get("overview", {})
                            .get("data", []),
                            "backgroundColor": [
                                "rgba(75, 192, 192, 0.2)",
                                "rgba(255, 206, 86, 0.2)",
                                "rgba(255, 99, 132, 0.2)",
                            ],
                            "borderColor": [
                                "rgba(75, 192, 192, 1)",
                                "rgba(255, 206, 86, 1)",
                                "rgba(255, 99, 132, 1)",
                            ],
                            "borderWidth": 1,
                        }
                    ],
                },
                "title": visual_analytics.get("engagement", {})
                .get("overview", {})
                .get("title", "Engagement Distribution"),
            },
            "view_distribution": {
                "type": visual_analytics.get("view_distribution", {})
                .get("chart", {})
                .get("type", "pie"),
                "data": {
                    "labels": visual_analytics.get("view_distribution", {})
                    .get("chart", {})
                    .get("labels", []),
                    "datasets": [
                        {
                            "data": visual_analytics.get("view_distribution", {})
                            .get("chart", {})
                            .get("data", []),
                            "backgroundColor": [
                                "rgba(255, 99, 132, 0.2)",
                                "rgba(54, 162, 235, 0.2)",
                                "rgba(255, 206, 86, 0.2)",
                                "rgba(75, 192, 192, 0.2)",
                                "rgba(153, 102, 255, 0.2)",
                                "rgba(255, 159, 64, 0.2)",
                            ],
                            "borderColor": [
                                "rgba(255, 99, 132, 1)",
                                "rgba(54, 162, 235, 1)",
                                "rgba(255, 206, 86, 1)",
                                "rgba(75, 192, 192, 1)",
                                "rgba(153, 102, 255, 1)",
                                "rgba(255, 159, 64, 1)",
                            ],
                            "borderWidth": 1,
                        }
                    ],
                },
                "title": visual_analytics.get("view_distribution", {})
                .get("chart", {})
                .get("title", "View Distribution"),
            },
            "timeline_analysis": {
                "type": visual_analytics.get("timeline", {})
                .get("chart", {})
                .get("type", "line"),
                "data": {
                    "labels": visual_analytics.get("timeline", {})
                    .get("chart", {})
                    .get("labels", []),
                    "datasets": visual_analytics.get("timeline", {})
                    .get("chart", {})
                    .get("datasets", []),
                },
                "title": visual_analytics.get("timeline", {})
                .get("chart", {})
                .get("title", "Timeline Analysis"),
            },
        }

        return jsonify(
            {
                "success": True,
                "chart_data": chart_data,
                "analytics_summary": {
                    "total_views": result.get("total_views", 0),
                    "total_likes": result.get("total_likes", 0),
                    "video_count": result.get("video_count", 0),
                    "engagement_rate": visual_analytics.get("engagement", {})
                    .get("metrics", {})
                    .get("avg_engagement", 0),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return (
            jsonify({"success": False, "error": "Failed to generate chart data"}),
            500,
        )
