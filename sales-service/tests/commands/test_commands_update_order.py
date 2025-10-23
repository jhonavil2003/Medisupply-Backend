import pytest
from decimal import Decimal
from src.commands.update_order import UpdateOrder
from src.errors.errors import NotFoundError, ApiError
from src.models.order import Order
from src.models.order_item import OrderItem


class TestUpdateOrderCommand:
    """Tests for UpdateOrder command with business rule validations."""
    
    # ==================== SUCCESSFUL UPDATE TESTS ====================
    
    def test_update_order_simple_fields(self, db, sample_order):
        """Test updating simple fields like delivery address."""
        update_data = {
            'delivery_address': 'Nueva Calle 123 #45-67',
            'delivery_city': 'Medellín',
            'delivery_department': 'Antioquia',
            'notes': 'Entrega urgente'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        assert result['id'] == sample_order.id
        assert result['delivery_address'] == 'Nueva Calle 123 #45-67'
        assert result['delivery_city'] == 'Medellín'
        assert result['delivery_department'] == 'Antioquia'
        assert result['notes'] == 'Entrega urgente'
    
    def test_update_order_payment_terms(self, db, sample_order):
        """Test updating payment terms and method."""
        update_data = {
            'payment_terms': 'credito_45',
            'payment_method': 'credito'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        assert result['payment_terms'] == 'credito_45'
        assert result['payment_method'] == 'credito'
    
    def test_update_order_status_pending_to_confirmed(self, db, sample_order):
        """Test valid status transition: PENDING → CONFIRMED."""
        update_data = {
            'status': 'confirmed'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        assert result['status'] == 'confirmed'
    
    def test_update_order_partial_update(self, db, sample_order):
        """Test partial update - only update specified fields."""
        original_address = sample_order.delivery_address
        original_payment_terms = sample_order.payment_terms
        
        update_data = {
            'notes': 'Solo actualizo notas'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Changed field
        assert result['notes'] == 'Solo actualizo notas'
        
        # Unchanged fields
        assert result['delivery_address'] == original_address
        assert result['payment_terms'] == original_payment_terms
    
    # ==================== ITEMS UPDATE TESTS ====================
    
    def test_update_order_items_replaces_completely(self, db, sample_order):
        """Test that updating items replaces all existing items."""
        # Original order has 2 items (JER-001 and VAC-001)
        original_items = OrderItem.query.filter_by(order_id=sample_order.id).all()
        assert len(original_items) == 2
        
        # Update with 1 new item
        update_data = {
            'items': [
                {
                    'product_sku': 'MASK-N95',
                    'product_name': 'Mascarilla N95',
                    'quantity': 50,
                    'unit_price': 5000.00,
                    'discount_percentage': 0.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verify only 1 item exists now
        updated_items = OrderItem.query.filter_by(order_id=sample_order.id).all()
        assert len(updated_items) == 1
        assert updated_items[0].product_sku == 'MASK-N95'
        assert updated_items[0].quantity == 50
    
    def test_update_order_items_recalculates_totals(self, db, sample_order):
        """Test that updating items recalculates order totals."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa 3ml',
                    'quantity': 10,
                    'unit_price': 1000.00,
                    'discount_percentage': 0.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Expected calculations:
        # Subtotal: 10 * 1000 = 10,000
        # Discount: 10,000 * 0% = 0
        # Tax: (10,000 - 0) * 19% = 1,900
        # Total: 10,000 - 0 + 1,900 = 11,900
        
        assert float(result['subtotal']) == 10000.00
        assert float(result['discount_amount']) == 0.00
        assert float(result['tax_amount']) == 1900.00
        assert float(result['total_amount']) == 11900.00
    
    def test_update_order_items_with_discount(self, db, sample_order):
        """Test items update with discount calculation."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'product_name': 'Jeringa 3ml',
                    'quantity': 100,
                    'unit_price': 500.00,
                    'discount_percentage': 10.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Expected calculations:
        # Subtotal: 100 * 500 = 50,000
        # Discount: 50,000 * 10% = 5,000
        # Tax: (50,000 - 5,000) * 19% = 8,550
        # Total: 50,000 - 5,000 + 8,550 = 53,550
        
        assert float(result['subtotal']) == 50000.00
        assert float(result['discount_amount']) == 5000.00
        assert float(result['tax_amount']) == 8550.00
        assert float(result['total_amount']) == 53550.00
    
    def test_update_order_multiple_items_with_different_taxes(self, db, sample_order):
        """Test updating with multiple items with different tax rates."""
        update_data = {
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Product 1',
                    'quantity': 10,
                    'unit_price': 1000.00,
                    'discount_percentage': 0.0,
                    'tax_percentage': 19.0
                },
                {
                    'product_sku': 'PROD-002',
                    'product_name': 'Product 2',
                    'quantity': 5,
                    'unit_price': 2000.00,
                    'discount_percentage': 5.0,
                    'tax_percentage': 5.0  # Different tax rate
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Item 1: subtotal=10,000, discount=0, tax=1,900
        # Item 2: subtotal=10,000, discount=500, tax=475
        # Total: subtotal=20,000, discount=500, tax=2,375, total=21,875
        
        assert float(result['subtotal']) == 20000.00
        assert float(result['discount_amount']) == 500.00
        assert float(result['tax_amount']) == 2375.00
        assert float(result['total_amount']) == 21875.00
    
    # ==================== VALIDATION ERROR TESTS ====================
    
    def test_update_order_not_found(self, db):
        """Test updating non-existent order raises NotFoundError."""
        update_data = {'notes': 'Test'}
        
        command = UpdateOrder(99999, update_data)
        
        with pytest.raises(NotFoundError) as exc_info:
            command.execute()
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_update_order_not_pending_returns_error(self, db, sample_order):
        """Test that only PENDING orders can be updated."""
        # Change order to confirmed
        sample_order.status = 'confirmed'
        db.session.commit()
        
        update_data = {'notes': 'Try to update'}
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "Solo se pueden editar órdenes pendientes" in str(exc_info.value)
    
    def test_update_order_invalid_status_transition(self, db, sample_order):
        """Test invalid status transitions are rejected."""
        update_data = {
            'status': 'cancelled'  # PENDING → CANCELLED not allowed
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "Invalid status transition" in str(exc_info.value)
    
    def test_update_order_items_empty_list_error(self, db, sample_order):
        """Test that items list cannot be empty."""
        update_data = {
            'items': []  # Empty list not allowed
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "at least one item" in str(exc_info.value).lower()
    
    def test_update_order_items_missing_product_sku(self, db, sample_order):
        """Test that product_sku is required in items."""
        update_data = {
            'items': [
                {
                    'quantity': 10,
                    'unit_price': 1000.00
                    # Missing product_sku
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "product_sku" in str(exc_info.value).lower()
    
    def test_update_order_items_missing_quantity(self, db, sample_order):
        """Test that quantity is required in items."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'unit_price': 1000.00
                    # Missing quantity
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "quantity" in str(exc_info.value).lower()
    
    def test_update_order_items_zero_quantity(self, db, sample_order):
        """Test that quantity must be greater than 0."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 0,  # Invalid: must be > 0
                    'unit_price': 1000.00
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "greater than 0" in str(exc_info.value).lower()
    
    def test_update_order_items_negative_quantity(self, db, sample_order):
        """Test that quantity cannot be negative."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': -5,  # Invalid: negative
                    'unit_price': 1000.00
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
    
    def test_update_order_items_not_a_list(self, db, sample_order):
        """Test that items must be a list."""
        update_data = {
            'items': 'not-a-list'  # Invalid type
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "must be a list" in str(exc_info.value).lower()
    
    # ==================== IMMUTABLE FIELDS TESTS ====================
    
    def test_update_order_ignores_immutable_customer_id(self, db, sample_order):
        """Test that customer_id is ignored silently."""
        original_customer_id = sample_order.customer_id
        
        update_data = {
            'customer_id': 99999,  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # customer_id should not change
        assert result['customer_id'] == original_customer_id
        # But other fields should update
        assert result['notes'] == 'Update notes'
    
    def test_update_order_ignores_immutable_seller_id(self, db, sample_order):
        """Test that seller_id is ignored silently."""
        original_seller_id = sample_order.seller_id
        
        update_data = {
            'seller_id': 'NEW-SELLER',  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # seller_id should not change
        assert result['seller_id'] == original_seller_id
        assert result['notes'] == 'Update notes'
    
    def test_update_order_ignores_immutable_order_number(self, db, sample_order):
        """Test that order_number is ignored silently."""
        original_order_number = sample_order.order_number
        
        update_data = {
            'order_number': 'ORD-FAKE-9999',  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # order_number should not change
        assert result['order_number'] == original_order_number
        assert result['notes'] == 'Update notes'
    
    def test_update_order_ignores_immutable_totals(self, db, sample_order):
        """Test that monetary totals are ignored (auto-calculated)."""
        update_data = {
            'subtotal': 999999.99,  # Try to change immutable field
            'total_amount': 999999.99,  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Totals should not change to the fake values
        assert float(result['subtotal']) != 999999.99
        assert float(result['total_amount']) != 999999.99
        # But other fields should update
        assert result['notes'] == 'Update notes'
    
    def test_update_order_ignores_multiple_immutable_fields(self, db, sample_order):
        """Test that multiple immutable fields are all ignored."""
        original_customer_id = sample_order.customer_id
        original_order_number = sample_order.order_number
        
        update_data = {
            'customer_id': 99999,
            'seller_id': 'FAKE-SELLER',
            'order_number': 'FAKE-ORDER',
            'created_at': '2099-12-31',
            'subtotal': 999999.99,
            'notes': 'Valid update'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # All immutable fields should remain unchanged
        assert result['customer_id'] == original_customer_id
        assert result['order_number'] == original_order_number
        # Valid field should update
        assert result['notes'] == 'Valid update'
    
    # ==================== EDGE CASES ====================
    
    def test_update_order_with_no_changes(self, db, sample_order):
        """Test updating with no real field changes but auto-confirms status."""
        # Order starts as pending
        assert sample_order.status == 'pending'
        
        update_data = {
            'notes': 'Same note'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Status should auto-confirm even with minimal changes
        assert result['status'] == 'confirmed'
    
    def test_update_order_returns_complete_data(self, db, sample_order):
        """Test that update returns complete order with items and customer."""
        update_data = {
            'notes': 'Test'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verify complete data is returned
        assert 'id' in result
        assert 'order_number' in result
        assert 'customer' in result
        assert 'items' in result
        assert len(result['items']) > 0
        
        # Verify customer data
        assert 'id' in result['customer']
        assert 'business_name' in result['customer']
    
    def test_update_order_preserves_existing_items_when_not_updated(self, db, sample_order):
        """Test that items are preserved when not included in update."""
        original_items = OrderItem.query.filter_by(order_id=sample_order.id).all()
        original_count = len(original_items)
        
        update_data = {
            'notes': 'Update without touching items'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Items should remain unchanged
        current_items = OrderItem.query.filter_by(order_id=sample_order.id).all()
        assert len(current_items) == original_count
        assert result['notes'] == 'Update without touching items'
