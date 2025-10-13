from src.models.order import Order


class GetOrders:
    """Command to get list of orders with optional filtering."""
    
    def __init__(self, customer_id=None, seller_id=None, status=None):
        self.customer_id = customer_id
        self.seller_id = seller_id
        self.status = status
    
    def execute(self):
        """
        Execute the command to retrieve orders.
        
        Returns:
            list: List of order dictionaries
        """
        query = Order.query
        
        # Apply filters
        if self.customer_id:
            query = query.filter(Order.customer_id == self.customer_id)
        
        if self.seller_id:
            query = query.filter(Order.seller_id == self.seller_id)
        
        if self.status:
            query = query.filter(Order.status == self.status)
        
        # Order by date (most recent first)
        query = query.order_by(Order.order_date.desc())
        
        orders = query.all()
        
        return [order.to_dict(include_items=True) for order in orders]
