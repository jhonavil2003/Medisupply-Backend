import pytest
from src.commands.delete_order import DeleteOrder
from src.models.order import Order
from src.models.order_item import OrderItem
from src.errors.errors import NotFoundError, ApiError


class TestDeleteOrderCommand:
    
    def test_delete_order_success(self, db, sample_order):
        """Test successful deletion of an order in PENDING status."""
        order_id = sample_order.id
        order_number = sample_order.order_number
        
        # Ensure order is in pending status
        assert sample_order.status == 'pending'
        
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
        
        # Ensure order is in pending status
        assert sample_order.status == 'pending'
        
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
    
    def test_delete_order_not_pending_raises_error(self, db, sample_order):
        """Test that deleting an order not in PENDING status raises ApiError."""
        # Change order status to confirmed
        sample_order.status = 'confirmed'
        db.session.commit()
        
        command = DeleteOrder(order_id=sample_order.id)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "Solo se pueden eliminar órdenes en estado 'pending'" in str(exc_info.value)
        assert "confirmed" in str(exc_info.value)
        
        # Verify order was NOT deleted
        order = Order.query.filter_by(id=sample_order.id).first()
        assert order is not None
        assert order.status == 'confirmed'
    
    def test_delete_order_shipped_status_raises_error(self, db, sample_order):
        """Test that deleting a SHIPPED order raises ApiError."""
        # Change order status to shipped
        sample_order.status = 'shipped'
        db.session.commit()
        
        command = DeleteOrder(order_id=sample_order.id)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "shipped" in str(exc_info.value)
    
    def test_delete_order_delivered_status_raises_error(self, db, sample_order):
        """Test that deleting a DELIVERED order raises ApiError."""
        # Change order status to delivered
        sample_order.status = 'delivered'
        db.session.commit()
        
        command = DeleteOrder(order_id=sample_order.id)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "delivered" in str(exc_info.value)
    
    def test_delete_order_returns_correct_info(self, db, sample_order):
        """Test that deleted order info contains all expected fields."""
        # Ensure order is in pending status
        assert sample_order.status == 'pending'
        
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
        assert deleted_info['status'] == 'pending'
