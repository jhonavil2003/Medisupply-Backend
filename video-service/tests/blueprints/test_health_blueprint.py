"""Tests para Health Blueprint"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask

from src.blueprints.health import health_bp


@pytest.fixture
def app():
    """Fixture para crear app Flask de prueba"""
    app = Flask(__name__)
    app.register_blueprint(health_bp)
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Fixture para cliente de prueba"""
    return app.test_client()


class TestHealthEndpoint:
    """Test suite para endpoint /health"""
    
    def test_health_check_returns_200(self, client):
        """Test que health check retorna 200"""
        response = client.get('/health')
        assert response.status_code == 200
    
    def test_health_check_returns_json(self, client):
        """Test que health check retorna JSON"""
        response = client.get('/health')
        assert response.content_type == 'application/json'
    
    def test_health_check_has_status(self, client):
        """Test que respuesta incluye status"""
        response = client.get('/health')
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_health_check_has_service_name(self, client):
        """Test que respuesta incluye nombre del servicio"""
        response = client.get('/health')
        data = response.get_json()
        assert 'service' in data
        assert data['service'] == 'video-service'
    
    def test_health_check_has_version(self, client):
        """Test que respuesta incluye versión"""
        response = client.get('/health')
        data = response.get_json()
        assert 'version' in data
        assert data['version'] == '1.0.0'
    
    def test_health_check_has_message(self, client):
        """Test que respuesta incluye mensaje"""
        response = client.get('/health')
        data = response.get_json()
        assert 'message' in data
        assert 'running' in data['message'].lower()
    
    def test_health_check_only_accepts_get(self, client):
        """Test que /health solo acepta GET"""
        response = client.post('/health')
        assert response.status_code == 405
