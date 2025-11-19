import pytest
from unittest.mock import Mock, patch
from src.services.integration_service import IntegrationService
from src.errors.errors import ExternalServiceError, ValidationError


class TestIntegrationService:
    
    @patch('src.services.integration_service.requests.get')
    def test_get_product_by_sku_success(self, mock_get):
        """Test successful product retrieval from catalog service."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 10ml',
            'unit_price': 1000.00,
            'is_active': True
        }
        mock_get.return_value = mock_response
        
        service = IntegrationService()
        result = service.get_product_by_sku('JER-001')
        
        assert result['sku'] == 'JER-001'
        assert result['is_active'] is True
        assert 'unit_price' in result
    
    @patch('src.services.integration_service.requests.get')
    def test_get_product_not_found(self, mock_get):
        """Test product not found raises ValidationError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        service = IntegrationService()
        
        with pytest.raises(ValidationError):
            service.get_product_by_sku('NONEXISTENT')
    
    @patch('src.services.integration_service.requests.get')
    def test_check_stock_availability_success(self, mock_get):
        """Test successful stock check."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Simular respuesta del endpoint de stock con las claves correctas
        # total_available_for_purchase ya incluye la resta de reservas
        mock_response.json.return_value = {
            'product_sku': 'JER-001',
            'total_available_for_purchase': 100,  # Este ya es el valor disponible para venta
            'total_physical_stock': 150,  # Stock físico total
            'total_reserved_in_carts': 50,  # Reservas temporales
            'distribution_centers': [{
                'distribution_center_code': 'DC-001',
                'available_for_purchase': 100  # Stock disponible en este centro
            }]
        }
        mock_get.return_value = mock_response
        
        service = IntegrationService()
        result = service.check_stock_availability('JER-001', 10)
        
        assert result['stock_confirmed'] is True
        assert result['total_available'] == 100
        assert result['selected_distribution_center'] == 'DC-001'
    
    @patch('src.services.integration_service.requests.get')
    def test_check_stock_with_preferred_center(self, mock_get):
        """Test stock check with preferred distribution center."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Simular respuesta con valores disponibles después de restar reservas
        mock_response.json.return_value = {
            'product_sku': 'JER-001',
            'total_available_for_purchase': 100,  # Ya incluye la resta de reservas
            'total_physical_stock': 150,
            'total_reserved_in_carts': 50,
            'distribution_centers': [
                {
                    'distribution_center_code': 'DC-001',
                    'available_for_purchase': 50  # Stock disponible en DC-001
                },
                {
                    'distribution_center_code': 'DC-002',
                    'available_for_purchase': 50  # Stock disponible en DC-002
                }
            ]
        }
        mock_get.return_value = mock_response
        
        service = IntegrationService()
        result = service.check_stock_availability('JER-001', 10, 'DC-002')
        
        assert result['stock_confirmed'] is True
        assert result['selected_distribution_center'] == 'DC-002'
    
    @patch('src.services.integration_service.IntegrationService.get_product_by_sku')
    @patch('src.services.integration_service.IntegrationService.check_stock_availability')
    def test_validate_order_items_success(self, mock_check_stock, mock_get_product):
        """Test successful validation of order items."""
        mock_get_product.return_value = {
            'sku': 'JER-001',
            'name': 'Jeringa 10ml',
            'unit_price': 1000.00,
            'is_active': True
        }
        
        mock_check_stock.return_value = {
            'stock_confirmed': True,
            'total_available': 100,
            'selected_distribution_center': 'DC-001'
        }
        
        service = IntegrationService()
        items = [{'product_sku': 'JER-001', 'quantity': 10}]
        result = service.validate_order_items(items)
        
        assert len(result) == 1
        assert result[0]['product_sku'] == 'JER-001'
        assert result[0]['stock_confirmed'] is True
    
    @patch('src.services.integration_service.IntegrationService.get_product_by_sku')
    @patch('src.services.integration_service.IntegrationService.check_stock_availability')
    def test_validate_order_items_multiple_products(self, mock_check_stock, mock_get_product):
        """Test validation of multiple order items."""
        def get_product_side_effect(sku):
            return {
                'sku': sku,
                'name': f'Product {sku}',
                'unit_price': 1000.00,
                'is_active': True
            }
        
        def check_stock_side_effect(sku, quantity, center=None):
            return {
                'stock_confirmed': True,
                'total_available': 100,
                'selected_distribution_center': 'DC-001'
            }
        
        mock_get_product.side_effect = get_product_side_effect
        mock_check_stock.side_effect = check_stock_side_effect
        
        service = IntegrationService()
        items = [
            {'product_sku': 'JER-001', 'quantity': 10},
            {'product_sku': 'VAC-001', 'quantity': 5}
        ]
        result = service.validate_order_items(items)
        
        assert len(result) == 2
        assert all(item['stock_confirmed'] for item in result)
