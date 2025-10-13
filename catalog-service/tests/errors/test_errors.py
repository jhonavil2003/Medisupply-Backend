import pytest
from flask import Flask
from werkzeug.exceptions import BadRequest
from src.errors.errors import ApiError, NotFoundError, ValidationError, DatabaseError


class TestApiError:
    
    def test_api_error_creation(self):
        error = ApiError("Test error")
        assert error.message == "Test error"
        assert error.status_code == 400
        assert error.payload is None
    
    def test_api_error_with_payload(self):
        payload = {'field': 'value'}
        error = ApiError("Error with payload", payload=payload)
        assert error.payload == payload
    
    def test_api_error_to_dict(self):
        error = ApiError("Test error", status_code=422)
        result = error.to_dict()
        
        assert result['error'] == "Test error"
        assert result['status_code'] == 422
    
    def test_api_error_to_dict_with_payload(self):
        payload = {'user_id': 123}
        error = ApiError("Action failed", payload=payload)
        result = error.to_dict()
        
        assert result['error'] == "Action failed"
        assert result['user_id'] == 123


class TestNotFoundError:
    
    def test_not_found_error_status_code(self):
        error = NotFoundError("Resource not found")
        assert error.status_code == 404


class TestValidationError:
    
    def test_validation_error_status_code(self):
        error = ValidationError("Invalid input")
        assert error.status_code == 400


class TestDatabaseError:
    
    def test_database_error_status_code(self):
        error = DatabaseError("Connection failed")
        assert error.status_code == 500


class TestErrorHandlers:
    
    def test_api_error_handler(self, app, client):
        @app.route('/test-api-error')
        def test_route():
            raise ApiError("Test API error", 422)
        
        response = client.get('/test-api-error')
        assert response.status_code == 422
        data = response.get_json()
        assert data['error'] == "Test API error"
    
    def test_not_found_error_handler(self, app, client):
        @app.route('/test-not-found')
        def test_route():
            raise NotFoundError("Test not found")
        
        response = client.get('/test-not-found')
        assert response.status_code == 404
    
    def test_validation_error_handler(self, app, client):
        @app.route('/test-validation')
        def test_route():
            raise ValidationError("Invalid data")
        
        response = client.get('/test-validation')
        assert response.status_code == 400
    
    def test_404_handler(self, app, client):
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_generic_exception_handler(self, app, client):
        @app.route('/test-exception')
        def test_route():
            raise Exception("Generic exception")
        
        response = client.get('/test-exception')
        assert response.status_code == 500
