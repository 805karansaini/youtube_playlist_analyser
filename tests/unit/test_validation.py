"""Unit tests for input validation module.

Tests the validation schemas and utilities to ensure proper input sanitization
and validation throughout the application.
"""

import pytest
from pydantic import ValidationError

from core.validation import (
    PlaylistUrlRequest,
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