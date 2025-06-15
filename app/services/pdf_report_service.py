"""PDF Report Generation Service for YouTube Playlist Analyzer.

This service generates professional PDF reports with charts, analysis,
and formatted data presentations.
"""

import io
from datetime import datetime
from typing import Dict, Any, List
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web apps
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
)
from reportlab.lib.colors import HexColor

from core.logging_config import get_logger, log_business_event


class PDFReportService:
    """Service for generating PDF reports from playlist analysis data."""

    def __init__(self):
        """Initialize the PDF report service."""
        self.logger = get_logger(__name__)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def generate_report(self, analysis_data: Dict[str, Any]) -> bytes:
        """Generate a comprehensive PDF report.

        Args:
            analysis_data: Dictionary containing playlist analysis results

        Returns:
            PDF report as bytes
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Build the report content
            story = []
            story.extend(self._create_title_page(analysis_data))
            story.append(PageBreak())
            story.extend(self._create_summary_section(analysis_data))
            story.append(PageBreak())
            story.extend(self._create_charts_section(analysis_data))
            story.append(PageBreak())
            story.extend(self._create_detailed_data_section(analysis_data))
            story.extend(self._create_footer_section())

            # Build the PDF
            doc.build(story)
            pdf_data = buffer.getvalue()
            buffer.close()

            # Get playlist_id and video_count from top-level or nested data
            nested_data = analysis_data.get("analysis_data", {})
            playlist_id = analysis_data.get(
                "playlist_id", nested_data.get("playlist_id")
            )
            video_count = analysis_data.get(
                "video_count", nested_data.get("video_count", 0)
            )

            log_business_event(
                event_type="pdf_report_generated",
                playlist_id=playlist_id,
                video_count=video_count,
            )

            return pdf_data

        except Exception as e:
            self.logger.error(f"PDF report generation failed: {str(e)}")
            raise ValueError(f"Failed to generate PDF report: {str(e)}")

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=1,  # Center alignment
            textColor=HexColor("#2E5BBA"),
        )

        self.heading_style = ParagraphStyle(
            "CustomHeading",
            parent=self.styles["Heading2"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=HexColor("#2E5BBA"),
        )

        self.subheading_style = ParagraphStyle(
            "CustomSubHeading",
            parent=self.styles["Heading3"],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=HexColor("#4A4A4A"),
        )

    def _create_title_page(self, analysis_data: Dict[str, Any]) -> List:
        """Create the title page of the report."""
        story = []

        # Main title
        story.append(Spacer(1, 2 * inch))
        title = Paragraph("YouTube Playlist Analysis Report", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.5 * inch))

        # Playlist information - handle both top-level and nested data
        nested_data = analysis_data.get("analysis_data", {})
        playlist_info = f"""
        <para alignment="center" fontSize="14" textColor="#666666">
        <b>Playlist ID:</b> {analysis_data.get("playlist_id", nested_data.get("playlist_id", "N/A"))}<br/>
        <b>Analysis Type:</b> {analysis_data.get("analysis_type", nested_data.get("analysis_type", "Basic")).title()}<br/>
        <b>Total Videos:</b> {analysis_data.get("video_count", nested_data.get("video_count", 0))}<br/>
        <b>Generated:</b> {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
        </para>
        """
        story.append(Paragraph(playlist_info, self.styles["Normal"]))
        story.append(Spacer(1, 1 * inch))

        # Summary box
        summary_text = analysis_data.get(
            "summary",
            nested_data.get(
                "summary",
                "Comprehensive analysis of YouTube playlist performance, engagement metrics, and content insights.",
            ),
        )
        summary_para = Paragraph(
            f'<para alignment="center" fontSize="12" textColor="#333333">{summary_text}</para>',
            self.styles["Normal"],
        )
        story.append(summary_para)

        return story

    def _create_summary_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create the summary section with key metrics."""
        story = []

        story.append(Paragraph("Executive Summary", self.heading_style))

        # Handle both top-level and nested data
        nested_data = analysis_data.get("analysis_data", {})

        # Key metrics table
        total_views = analysis_data.get(
            "total_views", nested_data.get("total_views", 0)
        )
        total_likes = analysis_data.get(
            "total_likes", nested_data.get("total_likes", 0)
        )

        metrics_data = [
            ["Metric", "Value"],
            [
                "Total Videos",
                f"{analysis_data.get('video_count', nested_data.get('video_count', 0)):,}",
            ],
            [
                "Total Duration",
                analysis_data.get(
                    "total_duration", nested_data.get("total_duration", "N/A")
                ),
            ],
            [
                "Average Duration",
                analysis_data.get(
                    "average_duration", nested_data.get("average_duration", "N/A")
                ),
            ],
            ["Total Views", f"{total_views:,}"],
            ["Total Likes", f"{total_likes:,}"],
        ]

        if total_views > 0 and total_likes > 0:
            engagement_rate = (total_likes / total_views) * 100
            metrics_data.append(["Engagement Rate", f"{engagement_rate:.2f}%"])

        metrics_table = Table(metrics_data, colWidths=[2.5 * inch, 2.5 * inch])
        metrics_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2E5BBA")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F5F5F5")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ]
            )
        )

        story.append(metrics_table)
        story.append(Spacer(1, 0.3 * inch))

        # Top performing videos
        videos = analysis_data.get("videos", [])
        if not videos:
            videos = nested_data.get("videos", [])
        if videos:
            story.append(Paragraph("Top Performing Videos", self.subheading_style))

            # Sort by view count and get top 5
            top_videos = sorted(
                videos, key=lambda x: x.get("view_count", 0), reverse=True
            )[:5]

            top_videos_data = [["Rank", "Title", "Views", "Likes"]]
            for i, video in enumerate(top_videos, 1):
                title = video.get("title", "")
                if len(title) > 50:
                    title = title[:47] + "..."
                top_videos_data.append(
                    [
                        str(i),
                        title,
                        f"{video.get('view_count', 0):,}",
                        f"{video.get('like_count', 0):,}",
                    ]
                )

            top_videos_table = Table(
                top_videos_data, colWidths=[0.5 * inch, 3 * inch, 1 * inch, 1 * inch]
            )
            top_videos_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4CAF50")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ]
                )
            )

            story.append(top_videos_table)

        return story

    def _create_charts_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create the charts and visualizations section."""
        story = []

        story.append(Paragraph("Data Visualizations", self.heading_style))

        # Handle both top-level and nested data for videos
        videos = analysis_data.get("videos", [])
        if not videos:
            videos = analysis_data.get("analysis_data", {}).get("videos", [])

        if not videos:
            story.append(
                Paragraph(
                    "No video data available for visualization.", self.styles["Normal"]
                )
            )
            return story

        # Create matplotlib charts and add them to the PDF
        charts = self._generate_matplotlib_charts(videos)

        for chart_title, chart_buffer in charts.items():
            story.append(Paragraph(chart_title, self.subheading_style))

            # Add chart image
            chart_buffer.seek(0)
            img = Image(chart_buffer, width=6 * inch, height=4 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))

        return story

    def _create_detailed_data_section(self, analysis_data: Dict[str, Any]) -> List:
        """Create the detailed data section."""
        story = []

        story.append(Paragraph("Detailed Video Data", self.heading_style))

        # Handle both top-level and nested data for videos
        videos = analysis_data.get("videos", [])
        if not videos:
            videos = analysis_data.get("analysis_data", {}).get("videos", [])

        if not videos:
            story.append(
                Paragraph("No detailed video data available.", self.styles["Normal"])
            )
            return story

        # Create detailed table (first 20 videos to avoid making PDF too large)
        videos_to_show = videos[:20]

        table_data = [["#", "Title", "Channel", "Views", "Likes", "Duration"]]

        for i, video in enumerate(videos_to_show, 1):
            title = video.get("title", "")
            if len(title) > 40:
                title = title[:37] + "..."

            channel = video.get("channel_title", "")
            if len(channel) > 20:
                channel = channel[:17] + "..."

            table_data.append(
                [
                    str(i),
                    title,
                    channel,
                    f"{video.get('view_count', 0):,}",
                    f"{video.get('like_count', 0):,}",
                    self._format_duration(video.get("duration", "")),
                ]
            )

        detailed_table = Table(
            table_data,
            colWidths=[
                0.3 * inch,
                2.2 * inch,
                1.2 * inch,
                0.8 * inch,
                0.8 * inch,
                0.7 * inch,
            ],
        )
        detailed_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), HexColor("#FF9800")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, HexColor("#F9F9F9")],
                    ),
                ]
            )
        )

        story.append(detailed_table)

        if len(videos) > 20:
            story.append(Spacer(1, 0.2 * inch))
            story.append(
                Paragraph(
                    f"<i>Note: Showing first 20 videos of {len(videos)} total videos. "
                    "Complete data available in CSV/Excel exports.</i>",
                    self.styles["Normal"],
                )
            )

        return story

    def _create_footer_section(self) -> List:
        """Create the footer section."""
        story = []

        story.append(Spacer(1, 0.5 * inch))
        footer_text = f"""
        <para alignment="center" fontSize="10" textColor="#888888">
        Generated by YouTube Playlist Analyzer<br/>
        Report created on {datetime.utcnow().strftime("%Y-%m-%d at %H:%M:%S UTC")}<br/>
        For more information, visit our documentation
        </para>
        """
        story.append(Paragraph(footer_text, self.styles["Normal"]))

        return story

    def _generate_matplotlib_charts(
        self, videos: List[Dict[str, Any]]
    ) -> Dict[str, io.BytesIO]:
        """Generate matplotlib charts and return as BytesIO buffers."""
        charts = {}

        # Set matplotlib style
        plt.style.use("default")
        plt.rcParams["figure.facecolor"] = "white"

        try:
            # 1. Top 10 Videos by Views
            top_videos = sorted(
                videos, key=lambda x: x.get("view_count", 0), reverse=True
            )[:10]
            if top_videos:
                fig, ax = plt.subplots(figsize=(10, 6))
                titles = [
                    (
                        v.get("title", "")[:20] + "..."
                        if len(v.get("title", "")) > 20
                        else v.get("title", "")
                    )
                    for v in top_videos
                ]
                views = [v.get("view_count", 0) for v in top_videos]

                bars = ax.bar(range(len(titles)), views, color="skyblue", alpha=0.8)
                ax.set_xlabel("Videos")
                ax.set_ylabel("View Count")
                ax.set_title("Top 10 Videos by View Count")
                ax.set_xticks(range(len(titles)))
                ax.set_xticklabels(titles, rotation=45, ha="right")

                # Add value labels on bars
                for bar, view in zip(bars, views):
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{view:,}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

                plt.tight_layout()

                buffer = io.BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                charts["Top Videos by Views"] = buffer
                plt.close()

            # 2. Engagement Rate Analysis
            engagement_videos = [
                v
                for v in videos
                if v.get("view_count", 0) > 0 and v.get("like_count", 0) > 0
            ][:15]
            if engagement_videos:
                fig, ax = plt.subplots(figsize=(10, 6))
                titles = [
                    (
                        v.get("title", "")[:15] + "..."
                        if len(v.get("title", "")) > 15
                        else v.get("title", "")
                    )
                    for v in engagement_videos
                ]
                engagement_rates = [
                    (v.get("like_count", 0) / v.get("view_count", 1)) * 100
                    for v in engagement_videos
                ]

                bars = ax.bar(
                    range(len(titles)), engagement_rates, color="lightcoral", alpha=0.8
                )
                ax.set_xlabel("Videos")
                ax.set_ylabel("Engagement Rate (%)")
                ax.set_title("Video Engagement Rate (Likes/Views)")
                ax.set_xticks(range(len(titles)))
                ax.set_xticklabels(titles, rotation=45, ha="right")

                # Add value labels on bars
                for bar, rate in zip(bars, engagement_rates):
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height,
                        f"{rate:.1f}%",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

                plt.tight_layout()

                buffer = io.BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                charts["Engagement Rate Analysis"] = buffer
                plt.close()

            # 3. Channel Distribution
            channel_counts = {}
            for video in videos:
                channel = video.get("channel_title", "Unknown")
                channel_counts[channel] = channel_counts.get(channel, 0) + 1

            if channel_counts:
                fig, ax = plt.subplots(figsize=(8, 8))

                # Get top 8 channels, group others as "Others"
                sorted_channels = sorted(
                    channel_counts.items(), key=lambda x: x[1], reverse=True
                )
                if len(sorted_channels) > 8:
                    top_channels = sorted_channels[:7]
                    others_count = sum(count for _, count in sorted_channels[7:])
                    top_channels.append(("Others", others_count))
                else:
                    top_channels = sorted_channels

                labels = [
                    channel[:15] + "..." if len(channel) > 15 else channel
                    for channel, _ in top_channels
                ]
                sizes = [count for _, count in top_channels]
                colors = plt.cm.Set3(range(len(labels)))

                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=labels,
                    autopct="%1.1f%%",
                    colors=colors,
                    startangle=90,
                )
                ax.set_title("Videos Distribution by Channel")

                plt.tight_layout()

                buffer = io.BytesIO()
                plt.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
                charts["Channel Distribution"] = buffer
                plt.close()

        except Exception as e:
            self.logger.error(f"Chart generation failed: {str(e)}")

        return charts

    def _format_duration(self, duration_str: str) -> str:
        """Format ISO 8601 duration to readable format."""
        if not duration_str or not duration_str.startswith("PT"):
            return "N/A"

        try:
            duration_str = duration_str[2:]  # Remove PT

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

            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"

        except Exception as e:
            self.logger.error(f"Error formatting duration: {str(e)}")
            return "N/A"
