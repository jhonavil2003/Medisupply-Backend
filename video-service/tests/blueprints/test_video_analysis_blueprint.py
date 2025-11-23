"""Tests para Video Analysis Blueprint"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from flask import Flask

from src.blueprints.video_analysis import video_analysis_bp
from src.errors.errors import ValidationError, ExternalServiceError


@pytest.fixture
def app():
    """Fixture para crear app Flask de prueba"""
    app = Flask(__name__)
    app.register_blueprint(video_analysis_bp)
    app.config['TESTING'] = True
    
    # Registrar error handlers
    from src.errors.errors import register_error_handlers
    register_error_handlers(app)
    
    return app


@pytest.fixture
def client(app):
    """Fixture para cliente de prueba"""
    return app.test_client()


class TestAnalyzeVideoEndpoint:
    """Test suite para endpoint POST /api/videos/analyze"""
    
    def test_analyze_requires_json_content_type(self, client):
        """Test que rechaza requests sin Content-Type JSON"""
        response = client.post('/api/videos/analyze', data='plain text')
        assert response.status_code in [400, 500]
    
    def test_analyze_requires_video_url(self, client):
        """Test que rechaza requests sin video_url"""
        response = client.post('/api/videos/analyze', json={})
        assert response.status_code in [400, 500]
    
    @patch('src.blueprints.video_analysis.AnalyzeVideoCommand')
    def test_analyze_validation_error_on_init(self, mock_command_class, client):
        """Test manejo de ValidationError en inicialización"""
        mock_command_class.side_effect = ValidationError("Invalid video URL")
        
        response = client.post('/api/videos/analyze', json={
            'video_url': 'invalid'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_analyze_only_accepts_post(self, client):
        """Test que solo acepta método POST"""
        response = client.get('/api/videos/analyze')
        assert response.status_code == 405  # Method Not Allowed
