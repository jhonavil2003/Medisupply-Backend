import pytest
from src.commands.delete_order import DeleteOrder
from src.models.order import Order
from src.models.order_item import OrderItem
from src.errors.errors import NotFoundError


class TestDeleteOrderCommand:
    
    def test_delete_order_success(self, db, sample_order):
        """Test successful deletion of an order."""
        order_id = sample_order.id
        order_number = sample_order.order_number
        
        command = DeleteOrder(order_id=order_id)
        result = command.execute()
        
        # Verify the result
        assert 'message' in result
        assert order_number in result['message']
        assert 'deleted_order' in result
        assert result['deleted_order']['id'] == order_id
        assert result['deleted_order']['order_number'] == order_number
        
        # Verify the order is actually deleted from the database
        deleted_order = Order.query.filter_by(id=order_id).first()
        assert deleted_order is None
    
    def test_delete_order_cascades_items(self, db, sample_order):
        """Test that deleting an order also deletes its items (cascade)."""
        order_id = sample_order.id
        
        # Count items before deletion
        items_count = OrderItem.query.filter_by(order_id=order_id).count()
        assert items_count >= 2  # sample_order has at least 2 items
        
        # Delete the order
        command = DeleteOrder(order_id=order_id)
        command.execute()
        
        # Verify items are also deleted
        remaining_items = OrderItem.query.filter_by(order_id=order_id).count()
        assert remaining_items == 0
    
    def test_delete_order_not_found(self, db):
        """Test deleting non-existent order raises NotFoundError."""
        command = DeleteOrder(order_id=99999)
        
        with pytest.raises(NotFoundError) as exc_info:
            command.execute()
        
        assert "Order with ID 99999 not found" in str(exc_info.value.message)
    
    def test_delete_order_returns_correct_info(self, db, sample_order):
        """Test that deleted order info contains all expected fields."""
        command = DeleteOrder(order_id=sample_order.id)
        result = command.execute()
        
        deleted_info = result['deleted_order']
        assert 'id' in deleted_info
        assert 'order_number' in deleted_info
        assert 'customer_id' in deleted_info
        assert 'seller_id' in deleted_info
        assert 'status' in deleted_info
        assert 'total_amount' in deleted_info
        
        # Verify values match original order
        assert deleted_info['customer_id'] == sample_order.customer_id
        assert deleted_info['seller_id'] == sample_order.seller_id
        assert deleted_info['status'] == sample_order.status
