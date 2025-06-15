"""Export routes for YouTube Playlist Analyzer.

This module provides Flask routes for exporting playlist analysis data
in various formats including CSV, Excel, JSON, and PDF reports.
"""

import io
from datetime import datetime, timezone

from core.logging_config import get_logger, log_business_event
from core.validation import (
    PlaylistUrlRequest,
    ExportRequest,
    JsonExportRequest,
    validate_request_data,
    ChartDataResponse,
    ExportFormatsResponse,
    ErrorResponse,
)
from flask import (
    Blueprint,
    current_app,
    g,
    jsonify,
    render_template,
    request,
    send_file,
)
from pydantic import ValidationError

# Create the blueprint
bp = Blueprint("export_routes", __name__, url_prefix="/api/export")
logger = get_logger(__name__)


@bp.route("/csv", methods=["POST"])
def export_csv():
    """Export playlist analysis data to CSV format.

    Expected JSON payload:
    {
        "playlist_url": "https://www.youtube.com/playlist?list=...",
        "analysis_type": "basic" (optional)
    }

    Returns:
        CSV file download
    """
    try:
        # Validate request data using Pydantic
        data = request.get_json()
        if not data:
            error_response = ErrorResponse(
                error="Bad Request", message="No JSON data provided"
            )
            return jsonify(error_response.model_dump()), 400

        try:
            export_request = validate_request_data(data, ExportRequest)
            playlist_id = export_request.playlist_url.split("list=")[-1].split("&")[0]
        except ValidationError as e:
            logger.warning(f"CSV export validation error: {str(e)}")
            error_response = ErrorResponse(
                error="Validation Error",
                message="Invalid request data",
                details=e.errors() if hasattr(e, "errors") else None,
            )
            return jsonify(error_response.model_dump()), 400
        except ValueError as e:
            logger.warning(f"CSV export validation error: {str(e)}")
            error_response = ErrorResponse(error="Validation Error", message=str(e))
            return jsonify(error_response.model_dump()), 400

        if not playlist_id:
            error_response = ErrorResponse(
                error="Invalid URL", message="Invalid playlist URL"
            )
            return jsonify(error_response.model_dump()), 400

        # Get services from container
        container = current_app.container
        analyzer_service = container.get_playlist_analyzer_service()
        export_service = container.get_export_service()

        # Get analysis data
        analysis_data = analyzer_service.analyze_playlist(export_request.playlist_url)

        # Export to CSV
        csv_data = export_service.export_to_csv(analysis_data)

        # Create file-like object
        output = io.BytesIO(csv_data)
        output.seek(0)

        filename = f"playlist_analysis_{playlist_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

        return send_file(
            output, mimetype="text/csv", as_attachment=True, download_name=filename
        )

    except Exception as e:
        logger.error(f"CSV export failed: {str(e)}")
        error_response = ErrorResponse(
            error="Export Failed", message="CSV export operation failed"
        )
        return jsonify(error_response.model_dump()), 500


@bp.route("/excel", methods=["POST"])
def export_excel():
    """Export playlist analysis data to Excel format with charts.

    Expected JSON payload:
    {
        "playlist_url": "https://www.youtube.com/playlist?list=...",
        "analysis_type": "basic" (optional)
    }

    Returns:
        Excel file download
    """
    try:
        # Validate request data using Pydantic
        data = request.get_json()
        if not data:
            error_response = ErrorResponse(
                error="Bad Request", message="No JSON data provided"
            )
            return jsonify(error_response.model_dump()), 400

        try:
            export_request = validate_request_data(data, ExportRequest)
            playlist_id = export_request.playlist_url.split("list=")[-1].split("&")[0]
        except ValidationError as e:
            logger.warning(f"Excel export validation error: {str(e)}")
            error_response = ErrorResponse(
                error="Validation Error",
                message="Invalid request data",
                details=e.errors() if hasattr(e, "errors") else None,
            )
            return jsonify(error_response.model_dump()), 400
        except ValueError as e:
            logger.warning(f"Excel export validation error: {str(e)}")
            error_response = ErrorResponse(error="Validation Error", message=str(e))
            return jsonify(error_response.model_dump()), 400

        if not playlist_id:
            error_response = ErrorResponse(
                error="Invalid URL", message="Invalid playlist URL"
            )
            return jsonify(error_response.model_dump()), 400

        # Get services from container
        container = current_app.container
        analyzer_service = container.get_playlist_analyzer_service()
        export_service = container.get_export_service()

        # Get analysis data
        analysis_data = analyzer_service.analyze_playlist(export_request.playlist_url)

        # Export to Excel
        excel_data = export_service.export_to_excel(analysis_data)

        # Create file-like object
        output = io.BytesIO(excel_data)
        output.seek(0)

        filename = f"playlist_analysis_{playlist_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return send_file(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        logger.error(f"Excel export failed: {str(e)}")
        error_response = ErrorResponse(
            error="Export Failed", message="Excel export operation failed"
        )
        return jsonify(error_response.model_dump()), 500


@bp.route("/json", methods=["POST"])
def export_json():
    """Export playlist analysis data to JSON format.

    Expected JSON payload:
    {
        "playlist_url": "https://www.youtube.com/playlist?list=...",
        "analysis_type": "basic" (optional),
        "pretty": true (optional)
    }

    Returns:
        JSON file download
    """
    try:
        # Validate request data using Pydantic
        data = request.get_json()
        if not data:
            error_response = ErrorResponse(
                error="Bad Request", message="No JSON data provided"
            )
            return jsonify(error_response.model_dump()), 400

        try:
            export_request = validate_request_data(data, JsonExportRequest)
            playlist_id = export_request.playlist_url.split("list=")[-1].split("&")[0]
        except ValidationError as e:
            logger.warning(f"JSON export validation error: {str(e)}")
            error_response = ErrorResponse(
                error="Validation Error",
                message="Invalid request data",
                details=e.errors() if hasattr(e, "errors") else None,
            )
            return jsonify(error_response.model_dump()), 400
        except ValueError as e:
            logger.warning(f"JSON export validation error: {str(e)}")
            error_response = ErrorResponse(error="Validation Error", message=str(e))
            return jsonify(error_response.model_dump()), 400

        if not playlist_id:
            error_response = ErrorResponse(
                error="Invalid URL", message="Invalid playlist URL"
            )
            return jsonify(error_response.model_dump()), 400

        # Get services from container
        container = current_app.container
        analyzer_service = container.get_playlist_analyzer_service()
        export_service = container.get_export_service()

        # Get analysis data
        analysis_data = analyzer_service.analyze_playlist(export_request.playlist_url)

        # Export to JSON
        json_data = export_service.export_to_json(analysis_data, export_request.pretty)

        # Create file-like object
        output = io.BytesIO(json_data)
        output.seek(0)

        filename = f"playlist_analysis_{playlist_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        return send_file(
            output,
            mimetype="application/json",
            as_attachment=True,
            download_name=filename,
        )

    except ValueError as e:
        logger.warning(f"JSON export validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"JSON export failed: {str(e)}")
        return jsonify({"error": "Export failed"}), 500


@bp.route("/pdf", methods=["POST"])
def export_pdf():
    """Export playlist analysis data to PDF report format.

    Expected JSON payload:
    {
        "playlist_url": "https://www.youtube.com/playlist?list=...",
        "analysis_type": "basic" (optional)
    }

    Returns:
        PDF file download
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        url_request = validate_request_data(data, ExportRequest)
        playlist_id = url_request.playlist_url.split("list=")[-1].split("&")[0]

        if not playlist_id:
            return jsonify({"error": "Invalid playlist URL"}), 400

        # Get services from container
        container = current_app.container
        analyzer_service = container.get_playlist_analyzer_service()
        pdf_service = container.get_pdf_report_service()

        # Get analysis data
        analysis_data = analyzer_service.analyze_playlist(url_request.playlist_url)

        # Generate PDF report
        pdf_data = pdf_service.generate_report(analysis_data)

        # Create file-like object
        output = io.BytesIO(pdf_data)
        output.seek(0)

        filename = f"playlist_report_{playlist_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except ValueError as e:
        logger.warning(f"PDF export validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"PDF export failed: {str(e)}")
        return jsonify({"error": "Export failed"}), 500


@bp.route("/chart-data", methods=["POST"])
def get_chart_data():
    """Get chart data for frontend visualizations.

    Expected JSON payload:
    {
        "playlist_url": "https://www.youtube.com/playlist?list=...",
        "analysis_type": "basic" (optional)
    }

    Returns:
        JSON with chart data for different visualization types
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        url_request = validate_request_data(data, PlaylistUrlRequest)
        playlist_id = url_request.get_playlist_id()

        if not playlist_id:
            return jsonify({"error": "Invalid playlist URL"}), 400

        # Get services from container
        container = current_app.container
        analyzer_service = container.get_playlist_analyzer_service()
        export_service = container.get_export_service()

        # Get analysis data
        analysis_data = analyzer_service.analyze_playlist(url_request.url)

        # Prepare chart data
        chart_data = export_service.prepare_chart_data(analysis_data)

        log_business_event(
            event_type="chart_data_generated",
            playlist_id=playlist_id,
            chart_types=list(chart_data.keys()),
        )

        # Create structured response using Pydantic model
        response = ChartDataResponse(
            playlist_id=playlist_id,
            chart_data=chart_data,
            metadata={
                "video_count": analysis_data.get("video_count", 0),
                "analysis_type": analysis_data.get("analysis_type", "basic"),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return jsonify(response.model_dump())

    except ValueError as e:
        logger.warning(f"Chart data validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Chart data generation failed: {str(e)}")
        return jsonify({"error": "Chart data generation failed"}), 500


@bp.route("/formats", methods=["GET"])
def get_export_formats():
    """Get available export formats and their descriptions.

    Returns:
        JSON with available export formats
    """
    formats = {
        "csv": {
            "name": "CSV",
            "description": "Comma-separated values format, suitable for spreadsheet applications",
            "mimetype": "text/csv",
            "endpoint": "/api/export/csv",
        },
        "excel": {
            "name": "Excel",
            "description": "Microsoft Excel format with charts and formatting",
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "endpoint": "/api/export/excel",
        },
        "json": {
            "name": "JSON",
            "description": "JavaScript Object Notation format for programmatic use",
            "mimetype": "application/json",
            "endpoint": "/api/export/json",
        },
        "pdf": {
            "name": "PDF Report",
            "description": "Professional PDF report with charts and analysis",
            "mimetype": "application/pdf",
            "endpoint": "/api/export/pdf",
        },
    }

    response = ExportFormatsResponse(
        formats=formats, chart_data_endpoint="/api/export/chart-data"
    )

    return jsonify(response.model_dump())


@bp.route("/download-page/<playlist_id>")
def download_page(playlist_id: str):
    """Render a download page for the given playlist.

    Args:
        playlist_id: YouTube playlist ID

    Returns:
        Rendered HTML template with download options
    """
    try:
        # Basic validation: ensure plausible playlist ID length (at least 12 characters)
        if not playlist_id or len(playlist_id) < 12:
            return render_template("error.html", error="Invalid playlist ID"), 400

        return render_template("download.html", playlist_id=playlist_id)

    except Exception as e:
        logger.error(f"Download page rendering failed: {str(e)}")
        return render_template("error.html", error="Page could not be loaded"), 500


# Error handlers specific to export routes
@bp.errorhandler(413)
def request_entity_too_large(error):
    """Handle request entity too large errors."""
    return (
        jsonify(
            {
                "error": "Request Too Large",
                "message": "The playlist is too large to export. Try limiting the number of videos.",
            }
        ),
        413,
    )


@bp.errorhandler(408)
def request_timeout(error):
    """Handle request timeout errors."""
    return (
        jsonify(
            {
                "error": "Request Timeout",
                "message": "Export operation took too long. Try again or use a smaller playlist.",
            }
        ),
        408,
    )


# Add request logging for export routes
@bp.before_request
def log_export_request():
    """Log export requests for monitoring."""
    logger.info(
        "Export request received",
        extra={
            "endpoint": request.endpoint,
            "method": request.method,
            "content_type": request.content_type,
            "request_id": getattr(g, "request_id", None),
        },
    )
