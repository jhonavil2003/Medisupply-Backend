"""
Tests para error handlers y custom exceptions.
"""

import pytest
from src.errors.errors import ApiError, NotFoundError, ValidationError, ConflictError


class TestApiError:
    """Tests para ApiError base class."""
    
    def test_api_error_default_status_code(self):
        """Test: ApiError tiene status code 400 por defecto."""
        error = ApiError("Test error")
        assert error.status_code == 400
        assert error.message == "Test error"
    
    def test_api_error_custom_status_code(self):
        """Test: ApiError con status code personalizado."""
        error = ApiError("Test error", status_code=418)
        assert error.status_code == 418
    
    def test_api_error_with_payload(self):
        """Test: ApiError con payload adicional."""
        payload = {'field': 'value', 'details': 'extra info'}
        error = ApiError("Test error", payload=payload)
        
        error_dict = error.to_dict()
        assert error_dict['error'] == "Test error"
        assert error_dict['status_code'] == 400
        assert error_dict['field'] == 'value'
        assert error_dict['details'] == 'extra info'
    
    def test_api_error_to_dict(self):
        """Test: ApiError.to_dict() retorna diccionario correcto."""
        error = ApiError("Test error", status_code=403)
        error_dict = error.to_dict()
        
        assert 'error' in error_dict
        assert 'status_code' in error_dict
        assert error_dict['error'] == "Test error"
        assert error_dict['status_code'] == 403
    
    def test_api_error_str(self):
        """Test: ApiError.__str__() retorna mensaje."""
        error = ApiError("Test error message")
        assert str(error) == "Test error message"


class TestNotFoundError:
    """Tests para NotFoundError."""
    
    def test_not_found_error_status_code(self):
        """Test: NotFoundError tiene status code 404."""
        error = NotFoundError("Resource not found")
        assert error.status_code == 404
        assert error.message == "Resource not found"
    
    def test_not_found_error_inheritance(self):
        """Test: NotFoundError hereda de ApiError."""
        error = NotFoundError("Not found")
        assert isinstance(error, ApiError)


class TestValidationError:
    """Tests para ValidationError."""
    
    def test_validation_error_status_code(self):
        """Test: ValidationError tiene status code 400."""
        error = ValidationError("Invalid data")
        assert error.status_code == 400
        assert error.message == "Invalid data"
    
    def test_validation_error_inheritance(self):
        """Test: ValidationError hereda de ApiError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, ApiError)


class TestConflictError:
    """Tests para ConflictError."""
    
    def test_conflict_error_status_code(self):
        """Test: ConflictError tiene status code 409."""
        error = ConflictError("Conflict detected")
        assert error.status_code == 409
        assert error.message == "Conflict detected"
    
    def test_conflict_error_inheritance(self):
        """Test: ConflictError hereda de ApiError."""
        error = ConflictError("Conflict")
        assert isinstance(error, ApiError)


class TestErrorHandlers:
    """Tests para error handlers de Flask."""
    
    def test_handle_api_error(self, client):
        """Test: Handler para ApiError personalizado."""
        # Provocar un ApiError a través de un endpoint
        response = client.post('/cart/reserve', json={
            'product_sku': 'TEST',
            'quantity': -5,  # Cantidad inválida
            'user_id': 'user1',
            'session_id': 'session1',
            'distribution_center_id': 1
        })
        
        # Debe retornar error 400
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data or 'success' in data
    
    def test_handle_not_found_error(self, client):
        """Test: Handler para NotFoundError."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'NOEXISTE999',
            'quantity': 5,
            'user_id': 'user1',
            'session_id': 'session1',
            'distribution_center_id': 1
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_handle_validation_error(self, client):
        """Test: Handler para ValidationError."""
        # Request sin campos requeridos
        response = client.post('/cart/reserve', json={
            'product_sku': 'TEST'
            # Faltan campos requeridos
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
