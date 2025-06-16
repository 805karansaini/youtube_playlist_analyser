"""Unit tests for export service functionality.

Tests the export service to ensure proper data export and visualization
functionality across different formats.
"""

import pytest
import json
import pandas as pd
from unittest.mock import patch

from services.export_service import ExportService


class TestExportService:
    """Test cases for ExportService."""

    @pytest.fixture
    def export_service(self):
        """Create export service instance for testing."""
        return ExportService()

    @pytest.fixture
    def sample_analysis_data(self):
        """Provide sample analysis data for testing."""
        return {
            'playlist_id': 'PLTest1234567890123456789012345',
            'analysis_type': 'basic',
            'video_count': 3,
            'total_duration': '15 minutes 30 seconds',
            'average_duration': '5 minutes 10 seconds',
            'total_views': 15000,
            'total_likes': 1500,
            'summary': 'Test playlist analysis summary',
            'videos': [
                {
                    'video_id': 'test_vid_1',
                    'title': 'Test Video 1',
                    'description': 'Test description 1',
                    'duration': 'PT5M30S',
                    'view_count': 5000,
                    'like_count': 500,
                    'published_at': '2023-01-01T00:00:00Z',
                    'channel_title': 'Test Channel'
                },
                {
                    'video_id': 'test_vid_2',
                    'title': 'Test Video 2',
                    'description': 'Test description 2',
                    'duration': 'PT10M00S',
                    'view_count': 10000,
                    'like_count': 1000,
                    'published_at': '2023-01-02T00:00:00Z',
                    'channel_title': 'Test Channel'
                }
            ]
        }

    def test_export_to_csv(self, export_service, sample_analysis_data):
        """Test CSV export functionality."""
        csv_data = export_service.export_to_csv(sample_analysis_data)
        
        assert isinstance(csv_data, bytes)
        csv_string = csv_data.decode('utf-8')
        
        # Check CSV headers
        assert 'Position' in csv_string
        assert 'Video ID' in csv_string
        assert 'Title' in csv_string
        assert 'View Count' in csv_string
        
        # Check data presence
        assert 'test_vid_1' in csv_string
        assert 'Test Video 1' in csv_string
        assert '5000' in csv_string

    def test_export_to_json(self, export_service, sample_analysis_data):
        """Test JSON export functionality."""
        json_data = export_service.export_to_json(sample_analysis_data, pretty=True)
        
        assert isinstance(json_data, bytes)
        json_string = json_data.decode('utf-8')
        parsed_json = json.loads(json_string)
        
        # Check JSON structure
        assert 'metadata' in parsed_json
        assert 'summary' in parsed_json
        assert 'videos' in parsed_json
        assert 'analysis_results' in parsed_json
        
        # Check metadata
        assert parsed_json['metadata']['playlist_id'] == 'PLTest1234567890123456789012345'
        assert parsed_json['metadata']['video_count'] == 3
        
        # Check videos data
        assert len(parsed_json['videos']) == 2
        assert parsed_json['videos'][0]['video_id'] == 'test_vid_1'

    def test_export_to_excel(self, export_service, sample_analysis_data):
        """Test Excel export functionality."""
        excel_data = export_service.export_to_excel(sample_analysis_data)
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
        
        # Verify it's a valid Excel file by checking the file signature
        assert excel_data.startswith(b'PK')  # Excel files are ZIP archives

    def test_prepare_chart_data(self, export_service, sample_analysis_data):
        """Test chart data preparation."""
        chart_data = export_service.prepare_chart_data(sample_analysis_data)
        
        assert isinstance(chart_data, dict)
        
        # Check required chart types
        expected_charts = [
            'video_performance', 'view_distribution', 'duration_analysis',
            'channel_breakdown', 'timeline_analysis', 'engagement_metrics'
        ]
        
        for chart_type in expected_charts:
            assert chart_type in chart_data
            if isinstance(chart_data[chart_type], dict) and 'error' not in chart_data[chart_type]:
                assert 'type' in chart_data[chart_type]
                assert 'title' in chart_data[chart_type]
                assert 'datasets' in chart_data[chart_type] or 'data' in chart_data[chart_type]

    def test_video_performance_chart(self, export_service, sample_analysis_data):
        """Test video performance chart data preparation."""
        videos = sample_analysis_data['videos']
        chart_data = export_service._prepare_video_performance_chart(videos)
        
        assert chart_data['type'] == 'bar'
        assert chart_data['title'] == 'Top 10 Videos by Views'
        assert len(chart_data['labels']) == 2
        assert len(chart_data['datasets'][0]['data']) == 2
        assert chart_data['datasets'][0]['data'][0] == 10000  # Higher view count first
        assert chart_data['datasets'][0]['data'][1] == 5000

    def test_view_distribution_chart(self, export_service, sample_analysis_data):
        """Test view distribution chart data preparation."""
        videos = sample_analysis_data['videos']
        chart_data = export_service._prepare_view_distribution_chart(videos)
        
        if 'error' not in chart_data:
            assert chart_data['type'] == 'pie'
            assert chart_data['title'] == 'View Count Distribution'
            assert 'labels' in chart_data
            assert 'datasets' in chart_data

    def test_duration_analysis_chart(self, export_service, sample_analysis_data):
        """Test duration analysis chart data preparation."""
        videos = sample_analysis_data['videos']
        chart_data = export_service._prepare_duration_analysis_chart(videos)
        
        assert chart_data['type'] == 'scatter'
        assert chart_data['title'] == 'Video Duration Analysis'
        assert 'datasets' in chart_data
        assert len(chart_data['datasets'][0]['data']) == 2

    def test_channel_breakdown_chart(self, export_service, sample_analysis_data):
        """Test channel breakdown chart data preparation."""
        videos = sample_analysis_data['videos']
        chart_data = export_service._prepare_channel_breakdown_chart(videos)
        
        assert chart_data['type'] == 'doughnut'
        assert chart_data['title'] == 'Videos by Channel'
        assert 'Test Channel' in chart_data['labels']
        assert chart_data['datasets'][0]['data'][0] == 2  # Both videos from same channel

    def test_parse_duration(self, export_service):
        """Test ISO 8601 duration parsing."""
        test_cases = [
            ('PT5M30S', 330),  # 5 minutes 30 seconds
            ('PT1H30M', 5400),  # 1 hour 30 minutes
            ('PT45S', 45),      # 45 seconds
            ('PT2H', 7200),     # 2 hours
            ('invalid', None),   # Invalid format
        ]
        
        for duration_str, expected_seconds in test_cases:
            result = export_service._parse_duration(duration_str)
            assert result == expected_seconds

    def test_prepare_dataframe(self, export_service, sample_analysis_data):
        """Test DataFrame preparation."""
        df = export_service._prepare_dataframe(sample_analysis_data)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert 'Position' in df.columns
        assert 'Video ID' in df.columns
        assert 'Title' in df.columns
        assert 'View Count' in df.columns
        
        # Check data values
        assert df.iloc[0]['Video ID'] == 'test_vid_1'
        assert df.iloc[1]['Video ID'] == 'test_vid_2'

    def test_prepare_summary_dataframe(self, export_service, sample_analysis_data):
        """Test summary DataFrame preparation."""
        summary_df = export_service._prepare_summary_dataframe(sample_analysis_data)
        
        assert isinstance(summary_df, pd.DataFrame)
        assert len(summary_df) > 0
        assert 'Metric' in summary_df.columns
        assert 'Value' in summary_df.columns
        
        # Check specific metrics
        metrics = summary_df['Metric'].tolist()
        assert 'Playlist ID' in metrics
        assert 'Total Videos' in metrics
        assert 'Total Views' in metrics

    def test_export_empty_data(self, export_service):
        """Test export with empty data."""
        empty_data = {
            'playlist_id': 'PLEmpty',
            'video_count': 0,
            'videos': []
        }
        
        # CSV export should work with empty data
        csv_data = export_service.export_to_csv(empty_data)
        assert isinstance(csv_data, bytes)
        
        # JSON export should work with empty data
        json_data = export_service.export_to_json(empty_data)
        assert isinstance(json_data, bytes)
        
        # Chart data should handle empty data gracefully
        chart_data = export_service.prepare_chart_data(empty_data)
        assert isinstance(chart_data, dict)

    def test_export_error_handling(self, export_service):
        """Test export error handling."""
        invalid_data = None
        
        with pytest.raises(ValueError):
            export_service.export_to_csv(invalid_data)
        
        with pytest.raises(ValueError):
            export_service.export_to_json(invalid_data)

    @patch('services.export_service.log_business_event')
    def test_logging_integration(self, mock_log, export_service, sample_analysis_data):
        """Test that exports are properly logged."""
        export_service.export_to_csv(sample_analysis_data)
        
        mock_log.assert_called_with(
            event_type="data_exported",
            format="csv",
            playlist_id='PLTest1234567890123456789012345',
            record_count=2
        )