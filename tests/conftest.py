"""Test configuration and fixtures for YouTube Playlist Analyzer.

This module provides pytest fixtures and configuration for testing
the YouTube Playlist Analyzer application.
"""

import os
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add app directory to Python path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app_factory import create_app
from core.config import Config
from core.container import Container


class TestConfig(Config):
    """Test configuration with safe defaults."""
    
    YOUTUBE_API_KEY: str = "test_api_key_123456789"
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    CACHE_TTL: int = 60
    MAX_RESULTS: int = 10


@pytest.fixture
def test_config() -> TestConfig:
    """Provide test configuration."""
    return TestConfig()


@pytest.fixture
def app(test_config: TestConfig):
    """Create test Flask application."""
    app = create_app(test_config)
    app.config['TESTING'] = True
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API client."""
    with patch('googleapiclient.discovery.build') as mock_build:
        mock_client = Mock()
        mock_build.return_value = mock_client
        
        # Mock playlist items response
        mock_client.playlistItems.return_value.list.return_value.execute.return_value = {
            'items': [
                {
                    'snippet': {
                        'title': 'Test Video 1',
                        'description': 'Test description 1',
                        'resourceId': {'videoId': 'test_video_1'},
                        'publishedAt': '2023-01-01T00:00:00Z',
                        'channelTitle': 'Test Channel'
                    },
                    'contentDetails': {
                        'videoId': 'test_video_1'
                    }
                },
                {
                    'snippet': {
                        'title': 'Test Video 2',
                        'description': 'Test description 2',
                        'resourceId': {'videoId': 'test_video_2'},
                        'publishedAt': '2023-01-02T00:00:00Z',
                        'channelTitle': 'Test Channel'
                    },
                    'contentDetails': {
                        'videoId': 'test_video_2'
                    }
                }
            ],
            'pageInfo': {
                'totalResults': 2,
                'resultsPerPage': 50
            }
        }
        
        # Mock video details response
        mock_client.videos.return_value.list.return_value.execute.return_value = {
            'items': [
                {
                    'id': 'test_video_1',
                    'statistics': {
                        'viewCount': '1000',
                        'likeCount': '100'
                    },
                    'contentDetails': {
                        'duration': 'PT5M30S'
                    }
                },
                {
                    'id': 'test_video_2',
                    'statistics': {
                        'viewCount': '2000',
                        'likeCount': '200'
                    },
                    'contentDetails': {
                        'duration': 'PT3M45S'
                    }
                }
            ]
        }
        
        yield mock_client


@pytest.fixture
def sample_playlist_data() -> Dict[str, Any]:
    """Provide sample playlist data for testing."""
    return {
        'playlist_id': 'PLTest1234567890123456789012345',
        'title': 'Test Playlist',
        'description': 'A test playlist for unit testing',
        'channel_title': 'Test Channel',
        'video_count': 2,
        'videos': [
            {
                'video_id': 'test_vid_1',
                'title': 'Test Video 1',
                'description': 'Test description 1',
                'duration': 'PT5M30S',
                'view_count': 1000,
                'like_count': 100,
                'published_at': '2023-01-01T00:00:00Z',
                'channel_title': 'Test Channel'
            },
            {
                'video_id': 'test_vid_2',
                'title': 'Test Video 2',
                'description': 'Test description 2',
                'duration': 'PT3M45S',
                'view_count': 2000,
                'like_count': 200,
                'published_at': '2023-01-02T00:00:00Z',
                'channel_title': 'Test Channel'
            }
        ]
    }


@pytest.fixture
def valid_playlist_urls() -> list[str]:
    """Provide valid YouTube playlist URLs for testing."""
    return [
        'https://www.youtube.com/playlist?list=PLTest1234567890123456789012345',
        'https://youtube.com/playlist?list=PLTest1234567890123456789012345',
        'https://m.youtube.com/playlist?list=PLTest1234567890123456789012345',
        'https://www.youtube.com/watch?v=abc123&list=PLTest1234567890123456789012345',
    ]


@pytest.fixture
def invalid_playlist_urls() -> list[str]:
    """Provide invalid YouTube playlist URLs for testing."""
    return [
        'https://example.com/playlist?list=PLTest1234567890123456789012345',
        'https://www.youtube.com/watch?v=abc123',
        'https://www.youtube.com/playlist?list=invalid_id',
        'not_a_url_at_all',
        '',
        'https://www.youtube.com/playlist',
    ]


@pytest.fixture
def mock_container():
    """Mock dependency container."""
    container = Mock(spec=Container)
    return container


@pytest.fixture
def mock_playlist_analyzer_service():
    """Mock playlist analyzer service."""
    service = Mock()
    service.analyze_playlist.return_value = {
        'playlist_id': 'PLTest1234567890123456789012345',
        'analysis_type': 'basic',
        'video_count': 2,
        'total_duration': '9 minutes 15 seconds',
        'average_duration': '4 minutes 37 seconds',
        'total_views': 3000,
        'total_likes': 300,
        'summary': 'Test playlist analysis summary'
    }
    return service


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'YOUTUBE_API_KEY': 'test_api_key_123456789',
        'ENVIRONMENT': 'testing',
        'LOG_LEVEL': 'DEBUG'
    }):
        yield


@pytest.fixture
def log_capture():
    """Capture log messages during tests."""
    import logging
    from io import StringIO
    
    log_capture_handler = logging.StreamHandler(StringIO())
    log_capture_handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger()
    logger.addHandler(log_capture_handler)
    
    yield log_capture_handler.stream
    
    logger.removeHandler(log_capture_handler)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as requiring API access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected test items."""
    # Add markers to tests based on their location
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)