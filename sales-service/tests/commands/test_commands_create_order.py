import pytest
from unittest.mock import Mock, patch
from decimal import Decimal
from src.commands.create_order import CreateOrder
from src.models.order import Order
from src.models.order_item import OrderItem
from src.errors.errors import ValidationError, NotFoundError


class TestCreateOrderCommand:
    """Test suite for CreateOrder command."""
    
    def test_create_order_success(self, db, sample_customer):
        """Test successful order creation with all required fields."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'seller_name': 'Juan Pérez',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'discount_percentage': 5.0
                }
            ],
            'payment_terms': 'credito_30',
            'payment_method': 'transferencia',
            'preferred_distribution_center': 'DC-BOG-001',
            'notes': 'Test order'
        }
        
        # Mock integration service
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify result structure
        assert 'id' in result
        assert 'order_number' in result
        assert result['customer_id'] == sample_customer.id
        assert result['seller_id'] == 'SELLER-001'
        assert result['seller_name'] == 'Juan Pérez'
        assert result['status'] == 'pending'
        assert result['payment_terms'] == 'credito_30'
        assert result['payment_method'] == 'transferencia'
        assert result['notes'] == 'Test order'
        
        # Verify order was saved to database
        order = Order.query.filter_by(id=result['id']).first()
        assert order is not None
        assert order.order_number == result['order_number']
        
        # Verify order items were created
        items = OrderItem.query.filter_by(order_id=order.id).all()
        assert len(items) == 1
        assert items[0].product_sku == 'JER-001'
        assert items[0].quantity == 10
    
    def test_create_order_with_multiple_items(self, db, sample_customer):
        """Test creating order with multiple items."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-002',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'discount_percentage': 5.0
                },
                {
                    'product_sku': 'VAC-001',
                    'quantity': 20,
                    'discount_percentage': 10.0
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                },
                {
                    'product_sku': 'VAC-001',
                    'product_name': 'Vacutainer EDTA',
                    'quantity': 20,
                    'unit_price': 2500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify order items
        assert 'items' in result
        assert len(result['items']) == 2
        
        # Verify items in database
        order = Order.query.filter_by(id=result['id']).first()
        items = OrderItem.query.filter_by(order_id=order.id).all()
        assert len(items) == 2
    
    def test_create_order_calculates_totals_correctly(self, db, sample_customer):
        """Test that order totals are calculated correctly."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'discount_percentage': 10.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Expected calculations:
        # Subtotal: 10 * 1000 = 10,000
        # Discount (10%): 1,000
        # After discount: 9,000
        # Tax (19%): 1,710
        # Total: 10,710
        
        assert float(result['subtotal']) == 9000.0
        assert float(result['discount_amount']) == 1000.0
        assert float(result['tax_amount']) == 1710.0
        assert float(result['total_amount']) == 10710.0
    
    def test_create_order_missing_customer_id(self, db):
        """Test that missing customer_id raises ValidationError."""
        order_data = {
            'seller_id': 'SELLER-001',
            'items': [{'product_sku': 'JER-001', 'quantity': 10}]
        }
        
        command = CreateOrder(order_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "Field 'customer_id' is required" in str(exc_info.value.message)
    
    def test_create_order_missing_seller_id(self, db, sample_customer):
        """Test that missing seller_id raises ValidationError."""
        order_data = {
            'customer_id': sample_customer.id,
            'items': [{'product_sku': 'JER-001', 'quantity': 10}]
        }
        
        command = CreateOrder(order_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "Field 'seller_id' is required" in str(exc_info.value.message)
    
    def test_create_order_missing_items(self, db, sample_customer):
        """Test that missing items raises ValidationError."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001'
        }
        
        command = CreateOrder(order_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "Field 'items' is required" in str(exc_info.value.message)
    
    def test_create_order_empty_items_list(self, db, sample_customer):
        """Test that empty items list raises ValidationError."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': []
        }
        
        command = CreateOrder(order_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        # Empty list is caught as "required" field validation
        assert "Field 'items' is required" in str(exc_info.value.message)
    
    def test_create_order_customer_not_found(self, db):
        """Test that non-existent customer raises NotFoundError."""
        order_data = {
            'customer_id': 99999,
            'seller_id': 'SELLER-001',
            'items': [{'product_sku': 'JER-001', 'quantity': 10}]
        }
        
        command = CreateOrder(order_data)
        
        with pytest.raises(NotFoundError) as exc_info:
            command.execute()
        
        assert "Customer with ID 99999 not found" in str(exc_info.value.message)
    
    def test_create_order_inactive_customer(self, db):
        """Test that inactive customer raises ValidationError."""
        # Create inactive customer
        from src.models.customer import Customer
        inactive_customer = Customer(
            document_type='NIT',
            document_number='900999999-9',
            business_name='Inactive Customer',
            trade_name='Inactive Customer',
            customer_type='hospital',
            contact_name='Test',
            contact_email='test@inactive.com',
            contact_phone='+57 1 1234567',
            address='Test Address',
            city='Bogotá',
            department='Cundinamarca',
            country='Colombia',
            is_active=False  # Inactive
        )
        db.session.add(inactive_customer)
        db.session.commit()
        
        order_data = {
            'customer_id': inactive_customer.id,
            'seller_id': 'SELLER-001',
            'items': [{'product_sku': 'JER-001', 'quantity': 10}]
        }
        
        command = CreateOrder(order_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "is not active" in str(exc_info.value.message)
    
    def test_create_order_uses_customer_defaults(self, db, sample_customer):
        """Test that order uses customer's default address when not provided."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                }
            ]
            # No delivery address provided
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify it uses customer's address
        assert result['delivery_address'] == sample_customer.address
        assert result['delivery_city'] == sample_customer.city
        assert result['delivery_department'] == sample_customer.department
    
    def test_create_order_generates_unique_order_number(self, db, sample_customer):
        """Test that each order gets a unique order number."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            # Create first order
            command1 = CreateOrder(order_data)
            result1 = command1.execute()
            
            # Create second order
            command2 = CreateOrder(order_data)
            result2 = command2.execute()
        
        # Verify different order numbers
        assert result1['order_number'] != result2['order_number']
        
        # Verify format (ORD-YYYYMMDD-XXXX)
        assert result1['order_number'].startswith('ORD-')
        assert result2['order_number'].startswith('ORD-')
    
    def test_create_order_includes_customer_info(self, db, sample_customer):
        """Test that result includes customer information."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify customer info is included
        assert 'customer' in result
        assert result['customer']['id'] == sample_customer.id
        assert result['customer']['business_name'] == sample_customer.business_name
    
    def test_create_order_includes_items_info(self, db, sample_customer):
        """Test that result includes items information."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify items are included
        assert 'items' in result
        assert len(result['items']) == 1
        assert result['items'][0]['product_sku'] == 'JER-001'
        assert result['items'][0]['product_name'] == 'Jeringa desechable 5ml'
        assert result['items'][0]['quantity'] == 10
    
    def test_create_order_sets_distribution_center_fallback(self, db, sample_customer):
        """Test that distribution center falls back to default when not provided."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                }
            ]
            # No preferred_distribution_center provided
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    # No distribution_center_code in item
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify items have default distribution center
        order = Order.query.filter_by(id=result['id']).first()
        items = OrderItem.query.filter_by(order_id=order.id).all()
        
        assert items[0].distribution_center_code == 'CEDIS-BOG'  # Default fallback
    
    def test_create_order_default_payment_terms(self, db, sample_customer):
        """Test that payment_terms defaults to 'contado' when not provided."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                }
            ]
            # No payment_terms provided
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1500.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify default payment terms
        assert result['payment_terms'] == 'contado'
    
    def test_create_order_default_tax_percentage(self, db, sample_customer):
        """Test that tax_percentage defaults to 19% when not provided."""
        order_data = {
            'customer_id': sample_customer.id,
            'seller_id': 'SELLER-001',
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10
                    # No tax_percentage provided
                }
            ]
        }
        
        with patch('src.commands.create_order.IntegrationService') as MockService:
            mock_instance = MockService.return_value
            mock_instance.validate_order_items.return_value = [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa desechable 5ml',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'distribution_center_code': 'DC-BOG-001',
                    'stock_confirmed': True
                }
            ]
            
            command = CreateOrder(order_data)
            result = command.execute()
        
        # Verify items have default tax (19%)
        order = Order.query.filter_by(id=result['id']).first()
        items = OrderItem.query.filter_by(order_id=order.id).all()
        
        assert float(items[0].tax_percentage) == 19.0
