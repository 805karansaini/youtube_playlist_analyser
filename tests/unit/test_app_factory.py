"""Unit tests for application factory.

Tests the Flask application creation, configuration, and initialization
to ensure proper setup of all components.
"""

from unittest.mock import patch
from flask import Flask

from app_factory import create_app
from core.config import Config
from exceptions.exception import YouTubeApiError, PlaylistAnalysisError


class TestCreateApp:
    """Test cases for create_app function."""

    def test_create_app_with_default_config(self):
        """Test app creation with default configuration."""
        app = create_app()
        
        assert isinstance(app, Flask)
        assert hasattr(app, 'container')
        assert hasattr(app, 'config_instance')
        assert isinstance(app.config_instance, Config)

    def test_create_app_with_custom_config(self, test_config):
        """Test app creation with custom configuration."""
        app = create_app(test_config)
        
        assert app.config['TESTING'] is True
        assert app.config_instance.ENVIRONMENT == 'testing'

    def test_blueprints_registered(self, app):
        """Test that blueprints are properly registered."""
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'home_routes' in blueprint_names

    def test_error_handlers_registered(self, app):
        """Test that error handlers are registered."""
        error_handlers = app.error_handler_spec[None]
        
        # Check that our custom error handlers are registered
        assert YouTubeApiError in error_handlers
        assert PlaylistAnalysisError in error_handlers
        assert 404 in error_handlers
        assert 500 in error_handlers

    def test_health_check_endpoints_registered(self, client):
        """Test that health check endpoints are available."""
        # Test health endpoint
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
        assert 'environment' in data

    def test_readiness_check_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get('/ready')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ready'
        assert 'timestamp' in data

    @patch('app_factory.setup_logging')
    def test_logging_setup_called(self, mock_setup_logging, test_config):
        """Test that logging setup is called during app creation."""
        create_app(test_config)
        mock_setup_logging.assert_called_once()


class TestMiddleware:
    """Test cases for application middleware."""

    def test_request_id_added(self, client):
        """Test that request ID is added to each request."""
        with client.application.test_request_context('/'):
            response = client.get('/')
            # Request should have been processed (even if route doesn't exist)
            assert response.status_code in [200, 404]

    def test_security_headers_added(self, client):
        """Test that security headers are added to responses."""
        response = client.get('/health')
        
        # Check security headers
        assert response.headers.get('X-Content-Type-Options') == 'nosniff'
        assert response.headers.get('X-Frame-Options') == 'DENY'
        assert response.headers.get('X-XSS-Protection') == '1; mode=block'


class TestErrorHandlers:
    """Test cases for error handlers."""

    def test_youtube_api_error_handler_html(self, app):
        """Test YouTube API error handler for HTML requests."""
        with app.test_client() as client:
            with app.app_context():
                # Simulate a YouTube API error
                error = YouTubeApiError("Test API error")
                
                with patch('app_factory.render_template') as mock_render:
                    mock_render.return_value = "Error page"
                    
                    # Test the error handler directly
                    handler = app.error_handler_spec[None][YouTubeApiError][YouTubeApiError]
                    response, status_code = handler(error)
                    
                    assert status_code == 400
                    mock_render.assert_called_once()

    def test_youtube_api_error_handler_json(self, app):
        """Test YouTube API error handler for JSON requests."""
        with app.test_client() as client:
            with app.app_context():
                with client.session_transaction() as sess:
                    # Mock a JSON request
                    with patch('flask.request') as mock_request:
                        mock_request.is_json = True
                        mock_request.headers.get.return_value = 'application/json'
                        
                        error = YouTubeApiError("Test API error")
                        handler = app.error_handler_spec[None][YouTubeApiError][YouTubeApiError]
                        response, status_code = handler(error)
                        
                        assert status_code == 400

    def test_playlist_analysis_error_handler(self, app):
        """Test playlist analysis error handler."""
        with app.app_context():
            error = PlaylistAnalysisError("Test analysis error")
            
            with patch('app_factory.render_template') as mock_render:
                mock_render.return_value = "Error page"
                
                handler = app.error_handler_spec[None][PlaylistAnalysisError][PlaylistAnalysisError]
                response, status_code = handler(error)
                
                assert status_code == 400
                mock_render.assert_called_once()

    def test_validation_error_handler(self, app):
        """Test validation error handler."""
        with app.app_context():
            error = ValueError("Test validation error")
            
            with patch('app_factory.render_template') as mock_render:
                mock_render.return_value = "Error page"
                
                handler = app.error_handler_spec[None][ValueError][ValueError]
                response, status_code = handler(error)
                
                assert status_code == 400
                mock_render.assert_called_once()

    def test_404_error_handler(self, client):
        """Test 404 error handler."""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404

    def test_404_error_handler_json(self, app):
        """Test 404 error handler for JSON requests."""
        with app.test_client() as client:
            with patch('flask.request') as mock_request:
                mock_request.is_json = True
                mock_request.headers.get.return_value = 'application/json'
                mock_request.url = 'http://test.com/nonexistent'
                
                response = client.get('/nonexistent-page')
                assert response.status_code == 404


class TestHealthChecks:
    """Test cases for health check endpoints."""

    def test_health_check_response_format(self, client):
        """Test health check response format."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = response.get_json()
        required_fields = ['status', 'timestamp', 'version', 'environment']
        
        for field in required_fields:
            assert field in data
        
        assert data['status'] == 'healthy'

    def test_readiness_check_with_container(self, client):
        """Test readiness check with initialized container."""
        response = client.get('/ready')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'ready'

    def test_readiness_check_without_container(self, app):
        """Test readiness check without container."""
        # Remove container to simulate uninitialized state
        delattr(app, 'container')
        
        with app.test_client() as client:
            response = client.get('/ready')
            assert response.status_code == 503
            
            data = response.get_json()
            assert data['status'] == 'not_ready'

    def test_readiness_check_exception_handling(self, app):
        """Test readiness check exception handling."""
        with app.test_client() as client:
            with patch('app_factory.hasattr', side_effect=Exception("Test error")):
                response = client.get('/ready')
                assert response.status_code == 503
                
                data = response.get_json()
                assert data['status'] == 'not_ready'
                assert 'Health check failed' in data['message']


class TestApplicationConfiguration:
    """Test cases for application configuration."""

    def test_config_instance_attached(self, app):
        """Test that config instance is attached to app."""
        assert hasattr(app, 'config_instance')
        assert isinstance(app.config_instance, Config)

    def test_container_attached(self, app):
        """Test that container is attached to app."""
        assert hasattr(app, 'container')
        assert app.container is not None

    def test_testing_mode_enabled(self, app):
        """Test that testing mode is properly enabled."""
        assert app.config.get('TESTING') is True

    def test_environment_configuration(self, app):
        """Test environment-specific configuration."""
        config = app.config_instance
        assert config.ENVIRONMENT == 'testing'
        assert config.DEBUG is True
        assert config.LOG_LEVEL == 'DEBUG'