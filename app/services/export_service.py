"""Data Export Service for YouTube Playlist Analyzer.

This service handles exporting playlist analysis data to various formats including
CSV, Excel, JSON, and provides data preparation for visualization.
"""

import json
import io
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.chart import BarChart

from core.logging_config import get_logger, log_business_event


class ExportService:
    """Service for exporting playlist analysis data to various formats."""

    def __init__(self):
        """Initialize the export service."""
        self.logger = get_logger(__name__)

    def export_to_csv(self, analysis_data: Dict[str, Any]) -> bytes:
        """Export analysis data to CSV format.

        Args:
            analysis_data: Dictionary containing playlist analysis results

        Returns:
            CSV data as bytes
        """
        try:
            # Convert to DataFrame
            df = self._prepare_dataframe(analysis_data)

            # Export to CSV
            output = io.StringIO()
            df.to_csv(output, index=False, encoding="utf-8")
            csv_data = output.getvalue().encode("utf-8")

            log_business_event(
                event_type="data_exported",
                format="csv",
                playlist_id=analysis_data.get("playlist_id"),
                record_count=len(df),
            )

            return csv_data

        except Exception as e:
            self.logger.error(f"CSV export failed: {str(e)}")
            raise ValueError(f"Failed to export CSV: {str(e)}")

    def export_to_excel(self, analysis_data: Dict[str, Any]) -> bytes:
        """Export analysis data to Excel format with charts and formatting.

        Args:
            analysis_data: Dictionary containing playlist analysis results

        Returns:
            Excel file data as bytes
        """
        try:
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                # Main data sheet
                df = self._prepare_dataframe(analysis_data)
                df.to_excel(writer, sheet_name="Video Data", index=False)

                # Summary sheet
                summary_df = self._prepare_summary_dataframe(analysis_data)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)

                # Format the Excel file
                workbook = writer.book
                self._format_excel_sheets(workbook, df, summary_df)

                # Add charts
                self._add_excel_charts(workbook, df)

            excel_data = output.getvalue()

            log_business_event(
                event_type="data_exported",
                format="excel",
                playlist_id=analysis_data.get("playlist_id"),
                record_count=len(df),
            )

            return excel_data

        except Exception as e:
            self.logger.error(f"Excel export failed: {str(e)}")
            raise ValueError(f"Failed to export Excel: {str(e)}")

    def export_to_json(
        self, analysis_data: Dict[str, Any], pretty: bool = True
    ) -> bytes:
        """Export analysis data to JSON format.

        Args:
            analysis_data: Dictionary containing playlist analysis results
            pretty: Whether to format JSON with indentation

        Returns:
            JSON data as bytes
        """
        try:
            # Extract videos from nested structure
            videos = analysis_data.get("videos", [])
            if not videos:
                videos = analysis_data.get("analysis_data", {}).get("videos", [])

            if not videos:
                self.logger.error("No videos found for JSON export")
                raise ValueError("No video data available for JSON export")

            # Extract summary data from both top-level and nested structure
            analysis_summary = analysis_data.get("analysis_data", {})

            # Prepare the data for JSON export
            export_data = {
                "metadata": {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "playlist_id": analysis_data.get(
                        "playlist_id", analysis_summary.get("playlist_id")
                    ),
                    "analysis_type": analysis_data.get(
                        "analysis_type", analysis_summary.get("analysis_type", "basic")
                    ),
                    "video_count": analysis_data.get(
                        "video_count", analysis_summary.get("video_count", len(videos))
                    ),
                },
                "summary": {
                    "total_duration": analysis_data.get(
                        "total_duration", analysis_summary.get("total_duration")
                    ),
                    "average_duration": analysis_data.get(
                        "average_duration", analysis_summary.get("average_duration")
                    ),
                    "total_views": analysis_data.get(
                        "total_views", analysis_summary.get("total_views")
                    ),
                    "total_likes": analysis_data.get(
                        "total_likes", analysis_summary.get("total_likes")
                    ),
                    "total_comments": analysis_data.get(
                        "total_comments", analysis_summary.get("total_comments")
                    ),
                    "summary_text": analysis_data.get(
                        "summary", analysis_summary.get("summary")
                    ),
                },
                "videos": videos,
                "analysis_results": analysis_data,
            }

            # Convert to JSON
            if pretty:
                json_str = json.dumps(
                    export_data, indent=2, ensure_ascii=False, default=str
                )
            else:
                json_str = json.dumps(export_data, ensure_ascii=False, default=str)

            json_data = json_str.encode("utf-8")

            log_business_event(
                event_type="data_exported",
                format="json",
                playlist_id=export_data["metadata"]["playlist_id"],
                record_count=len(videos),
            )

            return json_data

        except Exception as e:
            self.logger.error(f"JSON export failed: {str(e)}")
            raise ValueError(f"Failed to export JSON: {str(e)}")

    def prepare_chart_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for frontend charts and visualizations.

        Args:
            analysis_data: Dictionary containing playlist analysis results

        Returns:
            Dictionary with chart-ready data
        """
        try:
            # Try to get videos from different possible locations in analysis_data
            videos = analysis_data.get("videos", [])
            if not videos:
                videos = analysis_data.get("analysis_data", {}).get("videos", [])

            if not videos:
                self.logger.warning(
                    f"No video data found in analysis_data. Keys: {list(analysis_data.keys())}"
                )
                return {"error": "No video data available for visualization"}

            # Prepare different chart datasets
            chart_data = {
                "video_performance": self._prepare_video_performance_chart(videos),
                "view_distribution": self._prepare_view_distribution_chart(videos),
                "duration_analysis": self._prepare_duration_analysis_chart(videos),
                "channel_breakdown": self._prepare_channel_breakdown_chart(videos),
                "timeline_analysis": self._prepare_timeline_analysis_chart(videos),
                "engagement_metrics": self._prepare_engagement_metrics_chart(videos),
            }

            return chart_data

        except Exception as e:
            self.logger.error(f"Chart data preparation failed: {str(e)}")
            return {"error": f"Failed to prepare chart data: {str(e)}"}

    def _prepare_dataframe(self, analysis_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare a pandas DataFrame from analysis data."""
        # Try to get videos from different possible locations
        videos = analysis_data.get("videos", [])
        if not videos:
            videos = analysis_data.get("analysis_data", {}).get("videos", [])

        self.logger.info(
            f"DataFrame preparation: Found {len(videos)} videos. Analysis data keys: {list(analysis_data.keys())}"
        )

        if not videos:
            self.logger.error("No videos found in analysis data")
            raise ValueError("No video data available for export")

        # Flatten video data for DataFrame
        df_data = []
        for i, video in enumerate(videos, 1):
            # Log first video structure for debugging
            if i == 1:
                self.logger.info(f"First video structure: {list(video.keys())}")

            # Handle missing duration_seconds by calculating from duration_minutes
            duration_seconds = video.get("duration_seconds", 0)
            if not duration_seconds and video.get("duration_minutes"):
                duration_seconds = video.get("duration_minutes", 0) * 60

            row = {
                "Position": i,
                "Video ID": video.get("video_id", ""),
                "Title": video.get("title", ""),
                "Channel": video.get("channel_title", ""),
                "Duration (minutes)": round(video.get("duration_minutes", 0), 2),
                "Duration (seconds)": round(duration_seconds, 2),
                "View Count": video.get("view_count", 0),
                "Like Count": video.get("like_count", 0),
                "Comment Count": video.get("comment_count", 0),
                "Published Date": video.get("published_at", ""),
                "Description": (
                    video.get("description", "")[:100] + "..."
                    if video.get("description", "")
                    else ""
                ),
            }
            df_data.append(row)

        return pd.DataFrame(df_data)

    def _prepare_summary_dataframe(self, analysis_data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare a summary DataFrame."""
        # Try to get values from both top-level and nested analysis_data
        nested_data = analysis_data.get("analysis_data", {})

        summary_data = [
            ["Metric", "Value"],
            [
                "Playlist ID",
                analysis_data.get("playlist_id", nested_data.get("playlist_id", "")),
            ],
            [
                "Analysis Type",
                analysis_data.get(
                    "analysis_type", nested_data.get("analysis_type", "basic")
                ),
            ],
            [
                "Total Videos",
                analysis_data.get("video_count", nested_data.get("video_count", 0)),
            ],
            [
                "Total Duration",
                analysis_data.get(
                    "total_duration", nested_data.get("total_duration", "")
                ),
            ],
            [
                "Average Duration",
                analysis_data.get(
                    "average_duration", nested_data.get("average_duration", "")
                ),
            ],
            [
                "Total Views",
                analysis_data.get("total_views", nested_data.get("total_views", 0)),
            ],
            [
                "Total Likes",
                analysis_data.get("total_likes", nested_data.get("total_likes", 0)),
            ],
            [
                "Total Comments",
                analysis_data.get(
                    "total_comments", nested_data.get("total_comments", 0)
                ),
            ],
            ["Export Timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")],
        ]

        return pd.DataFrame(summary_data[1:], columns=summary_data[0])

    def _format_excel_sheets(
        self, workbook: Workbook, df: pd.DataFrame, summary_df: pd.DataFrame
    ):
        """Format Excel sheets with styling."""
        # Format Video Data sheet
        video_sheet = workbook["Video Data"]
        header_fill = PatternFill(
            start_color="366092", end_color="366092", fill_type="solid"
        )
        header_font = Font(color="FFFFFF", bold=True)

        # Style headers
        for cell in video_sheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        # Auto-adjust column widths
        for column in video_sheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception as e:
                    self.logger.error(f"Error formatting Excel sheet: {str(e)}")
            adjusted_width = min(max_length + 2, 50)
            video_sheet.column_dimensions[column_letter].width = adjusted_width

        # Format Summary sheet
        summary_sheet = workbook["Summary"]
        for cell in summary_sheet[1]:
            cell.fill = header_fill
            cell.font = header_font

        summary_sheet.column_dimensions["A"].width = 20
        summary_sheet.column_dimensions["B"].width = 30

    def _add_excel_charts(self, workbook: Workbook, df: pd.DataFrame):
        """Add charts to Excel workbook."""
        if df.empty:
            return

        # Create Charts sheet
        charts_sheet = workbook.create_sheet("Charts")

        # View Count Chart
        view_chart = BarChart()
        view_chart.title = "Video View Counts"
        view_chart.y_axis.title = "Views"
        view_chart.x_axis.title = "Videos (Top 10)"

        # Get top 10 videos by views
        top_videos = df.nlargest(10, "View Count")

        # Add chart to the Charts sheet if we have data
        if len(top_videos) > 0:
            charts_sheet["A1"] = "Top 10 Videos by Views"
            charts_sheet["A1"].font = Font(bold=True, size=14)

            # Add data for the chart
            start_row = 3
            charts_sheet.cell(start_row, 1, "Video Title")
            charts_sheet.cell(start_row, 2, "View Count")

            for i, (_, video) in enumerate(top_videos.iterrows(), start_row + 1):
                charts_sheet.cell(
                    i,
                    1,
                    (
                        video["Title"][:30] + "..."
                        if len(video["Title"]) > 30
                        else video["Title"]
                    ),
                )
                charts_sheet.cell(i, 2, video["View Count"])

    def _prepare_video_performance_chart(self, videos: List[Dict]) -> Dict[str, Any]:
        """Prepare data for video performance chart."""
        top_videos = sorted(videos, key=lambda x: x.get("view_count", 0), reverse=True)[
            :10
        ]

        return {
            "type": "bar",
            "title": "Top 10 Videos by Views",
            "labels": [
                (
                    v.get("title", "")[:30] + "..."
                    if len(v.get("title", "")) > 30
                    else v.get("title", "")
                )
                for v in top_videos
            ],
            "datasets": [
                {
                    "label": "View Count",
                    "data": [v.get("view_count", 0) for v in top_videos],
                    "backgroundColor": "rgba(54, 162, 235, 0.6)",
                    "borderColor": "rgba(54, 162, 235, 1)",
                    "borderWidth": 1,
                }
            ],
        }

    def _prepare_view_distribution_chart(self, videos: List[Dict]) -> Dict[str, Any]:
        """Prepare data for view distribution chart."""
        view_counts = [
            v.get("view_count", 0) for v in videos if v.get("view_count", 0) > 0
        ]

        if not view_counts:
            return {"error": "No view data available"}

        # Create view ranges
        max_views = max(view_counts)
        ranges = [
            f"0-{max_views // 4:,}",
            f"{max_views // 4:,}-{max_views // 2:,}",
            f"{max_views // 2:,}-{3 * max_views // 4:,}",
            f"{3 * max_views // 4:,}+",
        ]

        range_counts = [0, 0, 0, 0]
        for views in view_counts:
            if views <= max_views // 4:
                range_counts[0] += 1
            elif views <= max_views // 2:
                range_counts[1] += 1
            elif views <= 3 * max_views // 4:
                range_counts[2] += 1
            else:
                range_counts[3] += 1

        return {
            "type": "pie",
            "title": "View Count Distribution",
            "labels": ranges,
            "datasets": [
                {
                    "data": range_counts,
                    "backgroundColor": [
                        "rgba(255, 99, 132, 0.6)",
                        "rgba(54, 162, 235, 0.6)",
                        "rgba(255, 205, 86, 0.6)",
                        "rgba(75, 192, 192, 0.6)",
                    ],
                }
            ],
        }

    def _prepare_duration_analysis_chart(self, videos: List[Dict]) -> Dict[str, Any]:
        """Prepare data for duration analysis chart."""
        durations = []
        titles = []

        for video in videos:
            duration_str = video.get("duration", "")
            if duration_str:
                # Parse ISO 8601 duration (PT5M30S -> 330 seconds)
                duration_seconds = self._parse_duration(duration_str)
                if duration_seconds:
                    durations.append(duration_seconds / 60)  # Convert to minutes
                    title = video.get("title", "")
                    titles.append(title[:25] + "..." if len(title) > 25 else title)

        return {
            "type": "scatter",
            "title": "Video Duration Analysis",
            "datasets": [
                {
                    "label": "Duration (minutes)",
                    "data": [
                        {"x": i, "y": duration} for i, duration in enumerate(durations)
                    ],
                    "backgroundColor": "rgba(153, 102, 255, 0.6)",
                    "borderColor": "rgba(153, 102, 255, 1)",
                }
            ],
            "labels": titles,
        }

    def _prepare_channel_breakdown_chart(self, videos: List[Dict]) -> Dict[str, Any]:
        """Prepare data for channel breakdown chart."""
        channel_counts = {}

        for video in videos:
            channel = video.get("channel_title", "Unknown")
            channel_counts[channel] = channel_counts.get(channel, 0) + 1

        # Sort by count and take top 10
        sorted_channels = sorted(
            channel_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return {
            "type": "doughnut",
            "title": "Videos by Channel",
            "labels": [channel for channel, _ in sorted_channels],
            "datasets": [
                {
                    "data": [count for _, count in sorted_channels],
                    "backgroundColor": [
                        f"hsl({i * 30}, 70%, 60%)" for i in range(len(sorted_channels))
                    ],
                }
            ],
        }

    def _prepare_timeline_analysis_chart(self, videos: List[Dict]) -> Dict[str, Any]:
        """Prepare data for timeline analysis chart."""
        dates = {}

        for video in videos:
            published_at = video.get("published_at", "")
            if published_at:
                try:
                    # Extract date part (YYYY-MM-DD)
                    date = published_at.split("T")[0]
                    year_month = date[:7]  # YYYY-MM
                    dates[year_month] = dates.get(year_month, 0) + 1
                except Exception as e:
                    self.logger.error(
                        f"Error preparing timeline analysis chart: {str(e)}"
                    )
                    continue

        sorted_dates = sorted(dates.items())

        return {
            "type": "line",
            "title": "Video Publishing Timeline",
            "labels": [date for date, _ in sorted_dates],
            "datasets": [
                {
                    "label": "Videos Published",
                    "data": [count for _, count in sorted_dates],
                    "borderColor": "rgba(255, 99, 132, 1)",
                    "backgroundColor": "rgba(255, 99, 132, 0.2)",
                    "tension": 0.4,
                }
            ],
        }

    def _prepare_engagement_metrics_chart(self, videos: List[Dict]) -> Dict[str, Any]:
        """Prepare data for engagement metrics chart."""
        engagement_data = []
        labels = []

        for video in videos[:15]:  # Top 15 videos
            views = video.get("view_count", 0)
            likes = video.get("like_count", 0)

            if views > 0:
                engagement_rate = (likes / views) * 100
                engagement_data.append(engagement_rate)
                title = video.get("title", "")
                labels.append(title[:20] + "..." if len(title) > 20 else title)

        return {
            "type": "bar",
            "title": "Engagement Rate (Likes/Views %)",
            "labels": labels,
            "datasets": [
                {
                    "label": "Engagement Rate (%)",
                    "data": engagement_data,
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "borderWidth": 1,
                }
            ],
        }

    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse ISO 8601 duration string to seconds."""
        try:
            # Remove PT prefix
            if not duration_str.startswith("PT"):
                return None

            duration_str = duration_str[2:]

            # Parse hours, minutes, seconds
            hours = 0
            minutes = 0
            seconds = 0

            if "H" in duration_str:
                hours_str, duration_str = duration_str.split("H")
                hours = int(hours_str)

            if "M" in duration_str:
                minutes_str, duration_str = duration_str.split("M")
                minutes = int(minutes_str)

            if "S" in duration_str:
                seconds_str = duration_str.replace("S", "")
                seconds = int(seconds_str)

            return hours * 3600 + minutes * 60 + seconds

        except Exception as e:
            self.logger.error(f"Error parsing duration: {str(e)}")
            return None
