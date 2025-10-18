from src.models.order import Order
from src.session import db
from src.errors.errors import NotFoundError


class DeleteOrder:
    """Command to delete an order by ID."""
    
    def __init__(self, order_id):
        self.order_id = order_id
    
    def execute(self):
        """
        Execute the command to delete an order.
        
        Returns:
            dict: Confirmation message with deleted order details
            
        Raises:
            NotFoundError: If order not found
        """
        order = Order.query.filter_by(id=self.order_id).first()
        
        if not order:
            raise NotFoundError(f"Order with ID {self.order_id} not found")
        
        # Guardar información antes de eliminar
        order_info = {
            'id': order.id,
            'order_number': order.order_number,
            'customer_id': order.customer_id,
            'seller_id': order.seller_id,
            'status': order.status,
            'total_amount': float(order.total_amount) if order.total_amount else 0.0
        }
        
        # Eliminar la orden (cascade eliminará también los items)
        db.session.delete(order)
        db.session.commit()
        
        return {
            'message': f"Order {order.order_number} deleted successfully",
            'deleted_order': order_info
        }
