from src.models.order import Order
from src.session import db
from src.errors.errors import NotFoundError, ApiError


class DeleteOrder:
    """Command to delete an order by ID (only PENDING orders)."""
    
    def __init__(self, order_id):
        self.order_id = order_id
    
    def execute(self):
        """
        Execute the command to delete an order.
        Only allows deletion of orders in 'pending' status.
        
        Returns:
            dict: Confirmation message with deleted order details
            
        Raises:
            NotFoundError: If order not found (404)
            ApiError: If order is not in 'pending' status (400)
        """
        order = Order.query.filter_by(id=self.order_id).first()
        
        if not order:
            raise NotFoundError(f"Order with ID {self.order_id} not found")
        
        # Validate order status - only PENDING orders can be deleted
        if order.status != 'pending':
            raise ApiError(
                f"Solo se pueden eliminar órdenes en estado 'pending'. Esta orden está en estado '{order.status}'",
                status_code=400
            )
        
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
