import pytest
from src.commands.get_order_by_id import GetOrderById
from src.errors.errors import NotFoundError


class TestGetOrderByIdCommand:
    
    def test_get_order_by_id(self, db, sample_order):
        """Test getting order by ID."""
        command = GetOrderById(order_id=sample_order.id)
        result = command.execute()
        
        assert result['id'] == sample_order.id
        assert result['order_number'] == sample_order.order_number
        assert result['status'] == 'pending'
    
    def test_get_order_includes_items(self, db, sample_order):
        """Test that order includes items."""
        command = GetOrderById(order_id=sample_order.id)
        result = command.execute()
        
        assert 'items' in result
        assert len(result['items']) >= 2
        # Verify one of the items
        product_skus = [item['product_sku'] for item in result['items']]
        assert 'JER-001' in product_skus
    
    def test_get_order_includes_customer(self, db, sample_order, sample_customer):
        command = GetOrderById(order_id=sample_order.id)
        result = command.execute()
        
        assert 'customer' in result
        assert result['customer']['business_name'] == sample_customer.business_name
    
    def test_get_order_includes_all_fields(self, db, sample_order):
        command = GetOrderById(order_id=sample_order.id)
        result = command.execute()
        
        assert 'seller_id' in result
        assert 'order_date' in result
        assert 'subtotal' in result
        assert 'total_amount' in result
        assert 'payment_terms' in result
    
    def test_get_order_not_found(self, db):
        """Test getting non-existent order raises error."""
        command = GetOrderById(order_id=99999)
        
        with pytest.raises(NotFoundError):
            command.execute()
