"""Tests para Error Handlers"""

import pytest
from unittest.mock import Mock
from flask import Flask
from src.errors.errors import (
    ApiError,
    ExternalServiceError,
    ValidationError,
    NotFoundError,
    DatabaseError,
    register_error_handlers
)


class TestErrorClasses:
    """Test suite para clases de error personalizadas"""
    
    def test_api_error_creation(self):
        """Test creación de ApiError"""
        error = ApiError("Test error", status_code=500)
        assert error.message == "Test error"
        assert error.status_code == 500
    
    def test_external_service_error_creation(self):
        """Test creación de ExternalServiceError"""
        error = ExternalServiceError("External error", status_code=503)
        assert error.message == "External error"
        assert error.status_code == 503
    
    def test_validation_error_creation(self):
        """Test creación de ValidationError"""
        error = ValidationError("Validation failed", status_code=400)
        assert error.message == "Validation failed"
        assert error.status_code == 400
    
    def test_error_to_dict(self):
        """Test conversión de error a diccionario"""
        error = ApiError("Test", status_code=500)
        error_dict = error.to_dict()
        
        assert error_dict['error'] == "Test"
    
    def test_not_found_error_default_status(self):
        """Test NotFoundError con status code por defecto"""
        error = NotFoundError("Resource not found")
        assert error.status_code == 404
        assert error.message == "Resource not found"
    
    def test_database_error_default_status(self):
        """Test DatabaseError con status code por defecto"""
        error = DatabaseError("DB connection failed")
        assert error.status_code == 500
        assert error.message == "DB connection failed"
    
    def test_external_service_error_default_status(self):
        """Test ExternalServiceError con status code por defecto"""
        error = ExternalServiceError("RAG service down")
        assert error.status_code == 502
        assert error.message == "RAG service down"


class TestErrorHandlers:
    """Test suite para error handlers"""
    
    def test_register_error_handlers(self):
        """Test registro de error handlers en Flask app"""
        app = Flask(__name__)
        register_error_handlers(app)
        
        # Verificar que se registraron handlers
        assert len(app.error_handler_spec[None]) > 0
    
    def test_api_error_handler(self):
        """Test handler para ApiError"""
        app = Flask(__name__)
        register_error_handlers(app)
        
        with app.test_client() as client:
            # Crear una ruta de prueba que lance ApiError
            @app.route('/test-error')
            def test_error():
                raise ApiError("Test error", status_code=500)
            
            response = client.get('/test-error')
            
            assert response.status_code == 500
            assert b'Test error' in response.data
    
    def test_validation_error_handler(self):
        """Test handler para ValidationError"""
        app = Flask(__name__)
        register_error_handlers(app)
        
        with app.test_client() as client:
            @app.route('/test-validation')
            def test_validation():
                raise ValidationError("Invalid input")
            
            response = client.get('/test-validation')
            
            assert response.status_code == 400
            assert b'Invalid input' in response.data
    
    def test_external_service_error_handler(self):
        """Test handler para ExternalServiceError"""
        app = Flask(__name__)
        register_error_handlers(app)
        
        with app.test_client() as client:
            @app.route('/test-external')
            def test_external():
                raise ExternalServiceError("Service unavailable")
            
            response = client.get('/test-external')
            
            assert response.status_code == 502
            assert b'Service unavailable' in response.data
    
    def test_generic_exception_handler(self):
        """Test handler para excepciones genéricas"""
        app = Flask(__name__)
        register_error_handlers(app)
        
        with app.test_client() as client:
            @app.route('/test-exception')
            def test_exception():
                raise Exception("Unexpected error")
            
            response = client.get('/test-exception')
            
            assert response.status_code == 500
            assert 'error' in response.json
