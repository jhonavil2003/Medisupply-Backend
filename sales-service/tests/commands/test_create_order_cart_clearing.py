"""
Tests para la funcionalidad de limpieza automática de carrito en CreateOrder.

Verifica que:
1. El carrito se limpie automáticamente cuando se proporciona user_id/session_id
2. La orden se cree correctamente incluso si falla la limpieza del carrito
3. Los errores de limpieza se manejen apropiadamente
"""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import Timeout, ConnectionError
from src.commands.create_order import CreateOrder
from src.models.order import Order
from src.models.order_item import OrderItem


class TestCreateOrderCartClearing:
    """Tests para limpieza automática de carrito."""
    
    def test_create_order_clears_cart_when_user_session_provided(self, db, sample_customer):
        """
        Test que el carrito se limpia automáticamente cuando se proporcionan
        user_id y session_id.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'user_id': 'test_user_123',
            'session_id': 'test_session_456',
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        # Mock IntegrationService
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            # Mock requests.post para limpieza de carrito
            with patch('src.commands.create_order.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'success': True,
                    'cleared_count': 2,
                    'products_affected': ['PROD-001'],
                    'message': '2 reservas liberadas'
                }
                mock_post.return_value = mock_response
                
                # Ejecutar comando
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que la orden se creó
                assert 'id' in result
                assert result['status'] == 'pending'
                
                # Verificar que se intentó limpiar el carrito
                assert mock_post.called
                call_args = mock_post.call_args
                
                # Verificar URL llamada
                url = call_args[0][0] if call_args[0] else call_args.kwargs.get('url')
                assert '/cart/clear' in url
                
                # Verificar datos enviados
                json_data = call_args.kwargs.get('json')
                assert json_data['user_id'] == 'test_user_123'
                assert json_data['session_id'] == 'test_session_456'
                
                # Verificar timeout
                assert call_args.kwargs.get('timeout') == 3
    
    def test_create_order_without_user_session_skips_cart_clearing(self, db, sample_customer):
        """
        Test que NO se intenta limpiar el carrito cuando no se proporcionan
        user_id y session_id.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            # Sin user_id ni session_id
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            with patch('src.commands.create_order.requests.post') as mock_post:
                # Simular respuesta exitosa para reserva de inventario
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {'items_reserved': []}
                
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que la orden se creó
                assert 'id' in result
                assert result['status'] == 'pending'
                
                # Verificar que SOLO se llamó para reservar inventario, NO para limpiar carrito
                # Debe haber 1 llamada (reserve inventory), NO 2 (reserve + clear cart)
                assert mock_post.call_count == 1
                # Verificar que la llamada fue para reservar inventario
                call_url = mock_post.call_args[0][0]
                assert '/inventory/reserve-for-order' in call_url
    
    def test_create_order_succeeds_even_if_cart_clearing_fails_timeout(self, db, sample_customer):
        """
        Test que la orden se crea exitosamente incluso si la limpieza del
        carrito falla por timeout.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'user_id': 'test_user_timeout',
            'session_id': 'test_session_timeout',
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            # Mock timeout en limpieza de carrito
            with patch('src.commands.create_order.requests.post') as mock_post:
                mock_post.side_effect = Timeout("Connection timeout")
                
                # La orden debe crearse a pesar del timeout
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que la orden se creó exitosamente
                assert 'id' in result
                assert result['status'] == 'pending'
                
                # Verificar que se intentó limpiar
                assert mock_post.called
                
                # Verificar que la orden está en la BD
                order = Order.query.filter_by(id=result['id']).first()
                assert order is not None
    
    def test_create_order_succeeds_even_if_cart_clearing_fails_connection(self, db, sample_customer):
        """
        Test que la orden se crea exitosamente incluso si la limpieza del
        carrito falla por error de conexión.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'user_id': 'test_user_conn',
            'session_id': 'test_session_conn',
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            # Mock error de conexión
            with patch('src.commands.create_order.requests.post') as mock_post:
                mock_post.side_effect = ConnectionError("Cannot connect to service")
                
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que la orden se creó
                assert 'id' in result
                assert result['status'] == 'pending'
    
    def test_create_order_succeeds_even_if_cart_clearing_returns_error(self, db, sample_customer):
        """
        Test que la orden se crea exitosamente incluso si la limpieza del
        carrito retorna un error HTTP.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'user_id': 'test_user_err',
            'session_id': 'test_session_err',
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            # Mock respuesta de error del servidor
            with patch('src.commands.create_order.requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 500
                mock_response.json.return_value = {
                    'success': False,
                    'error': 'SERVER_ERROR'
                }
                mock_post.return_value = mock_response
                
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que la orden se creó a pesar del error
                assert 'id' in result
                assert result['status'] == 'pending'
    
    def test_create_order_with_only_user_id_skips_clearing(self, db, sample_customer):
        """
        Test que NO se intenta limpiar si solo se proporciona user_id sin session_id.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'user_id': 'test_user_only',
            # Sin session_id
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            with patch('src.commands.create_order.requests.post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {'items_reserved': []}
                
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que se llama a reserve-for-order pero NO a cart/clear
                assert mock_post.call_count == 1
                call_url = mock_post.call_args[0][0]
                assert '/inventory/reserve-for-order' in call_url
                assert '/cart/clear' not in call_url
    
    def test_create_order_with_only_session_id_skips_clearing(self, db, sample_customer):
        """
        Test que NO se intenta limpiar si solo se proporciona session_id sin user_id.
        """
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            # Sin user_id
            'session_id': 'test_session_only',
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Producto Test',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            with patch('src.commands.create_order.requests.post') as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = {'items_reserved': []}
                
                command = CreateOrder(order_data)
                result = command.execute()
                
                # Verificar que se llama a reserve-for-order pero NO a cart/clear
                assert mock_post.call_count == 1
                call_url = mock_post.call_args[0][0]
                assert '/inventory/reserve-for-order' in call_url
                assert '/cart/clear' not in call_url
