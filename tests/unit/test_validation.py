"""Unit tests for input validation module.

Tests the validation schemas and utilities to ensure proper input sanitization
and validation throughout the application.
"""

import pytest
from pydantic import ValidationError

from core.validation import (
    PlaylistUrlRequest,
    PlaylistAnalysisRequest,
    VideoMetadata,
    PlaylistMetadata,
    AnalysisResult,
    validate_request_data,
    sanitize_filename,
    extract_youtube_video_id,
)


class TestPlaylistUrlRequest:
    """Test cases for PlaylistUrlRequest validation."""

    def test_valid_playlist_urls(self, valid_playlist_urls):
        """Test validation of valid YouTube playlist URLs."""
        for url in valid_playlist_urls:
            request = PlaylistUrlRequest(url=url)
            assert request.url == url
            assert request.get_playlist_id() == 'PLTest1234567890123456789012345'

    def test_invalid_playlist_urls(self, invalid_playlist_urls):
        """Test validation rejection of invalid URLs."""
        for url in invalid_playlist_urls:
            with pytest.raises(ValidationError):
                PlaylistUrlRequest(url=url)

    def test_extract_playlist_id_valid(self):
        """Test playlist ID extraction from valid URLs."""
        test_cases = [
            ('https://www.youtube.com/playlist?list=PLTest1234567890123456789012345', 
             'PLTest1234567890123456789012345'),
            ('https://youtube.com/watch?v=abc&list=UUTest1234567890123456789012345', 
             'UUTest1234567890123456789012345'),
        ]
        
        for url, expected_id in test_cases:
            assert PlaylistUrlRequest.extract_playlist_id(url) == expected_id

    def test_extract_playlist_id_invalid(self):
        """Test playlist ID extraction from invalid URLs."""
        invalid_urls = [
            'https://www.youtube.com/watch?v=abc123',
            'https://example.com/playlist?list=PLTest1234567890123456789012345',
            'not_a_url',
        ]
        
        for url in invalid_urls:
            assert PlaylistUrlRequest.extract_playlist_id(url) is None

    def test_url_normalization(self):
        """Test URL normalization and whitespace handling."""
        url_with_whitespace = "  https://www.youtube.com/playlist?list=PLTest1234567890123456789012345  "
        request = PlaylistUrlRequest(url=url_with_whitespace)
        assert request.url == url_with_whitespace.strip()


class TestPlaylistAnalysisRequest:
    """Test cases for PlaylistAnalysisRequest validation."""

    def test_valid_analysis_request(self):
        """Test validation of valid analysis request."""
        request_data = {
            'playlist_url': 'https://www.youtube.com/playlist?list=PLTest1234567890123456789012345',
            'analysis_type': 'detailed',
            'max_videos': 100,
            'include_metadata': True
        }
        
        request = PlaylistAnalysisRequest(**request_data)
        assert request.playlist_url == request_data['playlist_url']
        assert request.analysis_type == 'detailed'
        assert request.max_videos == 100
        assert request.include_metadata is True

    def test_default_values(self):
        """Test default values for optional fields."""
        request = PlaylistAnalysisRequest(
            playlist_url='https://www.youtube.com/playlist?list=PLTest1234567890123456789012345'
        )
        
        assert request.analysis_type == 'basic'
        assert request.max_videos is None
        assert request.include_metadata is True

    def test_invalid_analysis_type(self):
        """Test validation rejection of invalid analysis types."""
        with pytest.raises(ValidationError):
            PlaylistAnalysisRequest(
                playlist_url='https://www.youtube.com/playlist?list=PLTest1234567890123456789012345',
                analysis_type='invalid_type'
            )

    def test_invalid_max_videos(self):
        """Test validation of max_videos constraints."""
        # Test negative value
        with pytest.raises(ValidationError):
            PlaylistAnalysisRequest(
                playlist_url='https://www.youtube.com/playlist?list=PLTest1234567890123456789012345',
                max_videos=-1
            )
        
        # Test value exceeding limit
        with pytest.raises(ValidationError):
            PlaylistAnalysisRequest(
                playlist_url='https://www.youtube.com/playlist?list=PLTest1234567890123456789012345',
                max_videos=1001
            )


class TestVideoMetadata:
    """Test cases for VideoMetadata validation."""

    def test_valid_video_metadata(self):
        """Test validation of valid video metadata."""
        metadata = VideoMetadata(
            video_id='test_vid_11',
            title='Test Video Title',
            description='Test video description',
            duration='PT5M30S',
            view_count=1000,
            like_count=100,
            published_at='2023-01-01T00:00:00Z',
            channel_title='Test Channel'
        )
        
        assert metadata.video_id == 'test_vid_11'
        assert metadata.title == 'Test Video Title'
        assert metadata.view_count == 1000

    def test_invalid_video_id(self):
        """Test validation rejection of invalid video IDs."""
        invalid_ids = ['short', 'toolongvideoid123', 'invalid@id']
        
        for video_id in invalid_ids:
            with pytest.raises(ValidationError):
                VideoMetadata(video_id=video_id, title='Test Title')

    def test_text_sanitization(self):
        """Test sanitization of text fields."""
        malicious_text = '<script>alert("xss")</script>Test Title'
        metadata = VideoMetadata(
            video_id='test_vid_11',
            title=malicious_text
        )
        
        # Should remove dangerous characters
        assert '<script>' not in metadata.title
        assert 'alert' not in metadata.title
        assert 'Test Title' in metadata.title

    def test_optional_fields(self):
        """Test handling of optional fields."""
        metadata = VideoMetadata(
            video_id='test_vid_11',
            title='Test Title'
        )
        
        assert metadata.description is None
        assert metadata.view_count is None
        assert metadata.like_count is None


class TestPlaylistMetadata:
    """Test cases for PlaylistMetadata validation."""

    def test_valid_playlist_metadata(self, sample_playlist_data):
        """Test validation of valid playlist metadata."""
        # Convert video data to VideoMetadata objects
        videos = [VideoMetadata(**video) for video in sample_playlist_data['videos']]
        
        metadata = PlaylistMetadata(
            playlist_id=sample_playlist_data['playlist_id'],
            title=sample_playlist_data['title'],
            description=sample_playlist_data['description'],
            channel_title=sample_playlist_data['channel_title'],
            video_count=sample_playlist_data['video_count'],
            videos=videos
        )
        
        assert metadata.playlist_id == sample_playlist_data['playlist_id']
        assert len(metadata.videos) == 2

    def test_invalid_playlist_id(self):
        """Test validation rejection of invalid playlist IDs."""
        invalid_ids = ['short', 'invalid_format', 'AB123']
        
        for playlist_id in invalid_ids:
            with pytest.raises(ValidationError):
                PlaylistMetadata(
                    playlist_id=playlist_id,
                    title='Test Playlist',
                    video_count=0
                )


class TestAnalysisResult:
    """Test cases for AnalysisResult validation."""

    def test_valid_analysis_result(self):
        """Test validation of valid analysis result."""
        result = AnalysisResult(
            playlist_id='PLTest1234567890123456789012345',
            analysis_type='basic',
            video_count=10,
            total_duration='50 minutes',
            total_views=10000,
            summary='Test analysis summary'
        )
        
        assert result.playlist_id == 'PLTest1234567890123456789012345'
        assert result.video_count == 10
        assert result.total_views == 10000

    def test_negative_counts_rejected(self):
        """Test rejection of negative counts."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                playlist_id='PLTest1234567890123456789012345',
                analysis_type='basic',
                video_count=-1
            )

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                playlist_id='PLTest1234567890123456789012345',
                analysis_type='basic',
                video_count=10,
                extra_field='not_allowed'
            )


class TestValidationUtilities:
    """Test cases for validation utility functions."""

    def test_validate_request_data_success(self):
        """Test successful request data validation."""
        data = {
            'url': 'https://www.youtube.com/playlist?list=PLTest1234567890123456789012345'
        }
        
        result = validate_request_data(data, PlaylistUrlRequest)
        assert isinstance(result, PlaylistUrlRequest)
        assert result.url == data['url']

    def test_validate_request_data_failure(self):
        """Test request data validation failure."""
        data = {'url': 'invalid_url'}
        
        with pytest.raises(ValueError, match="Validation failed"):
            validate_request_data(data, PlaylistUrlRequest)

    def test_sanitize_filename(self):
        """Test filename sanitization."""
        test_cases = [
            ('normal_file.txt', 'normal_file.txt'),
            ('file with spaces.txt', 'file with spaces.txt'),
            ('file<with>bad:chars.txt', 'filewithbadchars.txt'),
            ('../../etc/passwd', 'etcpasswd'),
            ('', 'untitled'),
            ('   ', 'untitled'),
            ('.' * 300, '.' * 255),  # Test length limit
        ]
        
        for original, expected in test_cases:
            result = sanitize_filename(original)
            assert result == expected

    def test_extract_youtube_video_id(self):
        """Test YouTube video ID extraction."""
        test_cases = [
            ('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
            ('https://youtu.be/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
            ('https://www.youtube.com/embed/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
            ('https://example.com/video', None),
            ('invalid_url', None),
        ]
        
        for url, expected_id in test_cases:
            result = extract_youtube_video_id(url)
            assert result == expected_id