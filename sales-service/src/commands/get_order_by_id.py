from src.models.order import Order
from src.errors.errors import NotFoundError


class GetOrderById:
    """Command to get an order by ID."""
    
    def __init__(self, order_id):
        self.order_id = order_id
    
    def execute(self):
        """
        Execute the command to retrieve an order.
        
        Returns:
            dict: Order dictionary with items and customer
            
        Raises:
            NotFoundError: If order not found
        """
        order = Order.query.filter_by(id=self.order_id).first()
        
        if not order:
            raise NotFoundError(f"Order with ID {self.order_id} not found")
        
        return order.to_dict(include_items=True, include_customer=True)
