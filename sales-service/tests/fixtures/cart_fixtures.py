"""
Fixture adicional para tests de CreateOrder con limpieza de carrito.

Este archivo contiene mocks y fixtures para probar la nueva funcionalidad
de limpieza automática de carrito.
"""

import pytest
from unittest.mock import Mock, patch
from requests import Response


@pytest.fixture
def mock_cart_clear_success():
    """Mock exitoso de limpieza de carrito."""
    with patch('src.commands.create_order.requests.post') as mock_post:
        # Configurar respuesta exitosa
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'cleared_count': 3,
            'products_affected': ['PROD-001', 'PROD-002'],
            'message': '3 reservas liberadas'
        }
        mock_post.return_value = mock_response
        
        yield mock_post


@pytest.fixture
def mock_cart_clear_timeout():
    """Mock de timeout en limpieza de carrito."""
    with patch('src.commands.create_order.requests.post') as mock_post:
        # Configurar timeout
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Connection timeout")
        
        yield mock_post


@pytest.fixture
def mock_cart_clear_connection_error():
    """Mock de error de conexión en limpieza de carrito."""
    with patch('src.commands.create_order.requests.post') as mock_post:
        # Configurar error de conexión
        from requests.exceptions import ConnectionError
        mock_post.side_effect = ConnectionError("Cannot connect to service")
        
        yield mock_post


@pytest.fixture
def mock_cart_clear_server_error():
    """Mock de error del servidor en limpieza de carrito."""
    with patch('src.commands.create_order.requests.post') as mock_post:
        # Configurar respuesta de error
        mock_response = Mock(spec=Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Error interno del servidor'
        }
        mock_post.return_value = mock_response
        
        yield mock_post


# Decorator para usar en tests que no necesitan limpieza de carrito
def skip_cart_clear(test_func):
    """
    Decorator para tests que no incluyen user_id/session_id.
    
    Mockea requests.post pero no espera que sea llamado.
    """
    def wrapper(*args, **kwargs):
        with patch('src.commands.create_order.requests.post') as mock_post:
            result = test_func(*args, **kwargs)
            # Verificar que NO se intentó limpiar carrito
            mock_post.assert_not_called()
            return result
    return wrapper


# Helper para tests con limpieza de carrito
class CartClearHelper:
    """Helper class para verificar limpieza de carrito en tests."""
    
    @staticmethod
    def assert_cart_cleared(mock_post, user_id, session_id):
        """
        Verifica que se intentó limpiar el carrito con los datos correctos.
        
        Args:
            mock_post: Mock de requests.post
            user_id: ID de usuario esperado
            session_id: ID de sesión esperado
        """
        assert mock_post.called, "No se intentó limpiar el carrito"
        
        # Verificar la llamada
        call_args = mock_post.call_args
        
        # Verificar JSON enviado
        json_data = call_args.kwargs.get('json')
        assert json_data is not None, "No se envió JSON al limpiar carrito"
        assert json_data.get('user_id') == user_id, f"user_id incorrecto: {json_data.get('user_id')}"
        assert json_data.get('session_id') == session_id, f"session_id incorrecto: {json_data.get('session_id')}"
        
        # Verificar timeout configurado
        timeout = call_args.kwargs.get('timeout')
        assert timeout == 3, f"Timeout incorrecto: {timeout}"
    
    @staticmethod
    def assert_cart_not_cleared(mock_post):
        """
        Verifica que NO se intentó limpiar el carrito.
        
        Args:
            mock_post: Mock de requests.post
        """
        assert not mock_post.called, "Se intentó limpiar carrito cuando no debía"


# Ejemplo de uso en tests:
"""
def test_create_order_with_cart_clearing(db, sample_customer, mock_cart_clear_success):
    order_data = {
        'customer_id': sample_customer.id,
        'seller_id': 'SELLER-001',
        'user_id': 'test_user',
        'session_id': 'test_session',
        'items': [{'product_sku': 'PROD-001', 'quantity': 10}]
    }
    
    with patch('src.commands.create_order.IntegrationService') as MockService:
        mock_instance = MockService.return_value
        mock_instance.validate_order_items.return_value = [...]
        
        command = CreateOrder(order_data)
        result = command.execute()
    
    # Verificar que se limpió el carrito
    CartClearHelper.assert_cart_cleared(
        mock_cart_clear_success, 
        'test_user', 
        'test_session'
    )

def test_create_order_without_cart(db, sample_customer):
    order_data = {
        'customer_id': sample_customer.id,
        'seller_id': 'SELLER-001',
        # Sin user_id ni session_id
        'items': [{'product_sku': 'PROD-001', 'quantity': 10}]
    }
    
    with patch('src.commands.create_order.requests.post') as mock_post:
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [...]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verificar que NO se intentó limpiar carrito
        CartClearHelper.assert_cart_not_cleared(mock_post)
"""
