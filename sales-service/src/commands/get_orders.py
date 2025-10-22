from datetime import datetime
from src.models.order import Order


class GetOrders:
    """Command to get list of orders with optional filtering."""
    
    def __init__(self, customer_id=None, seller_id=None, status=None, 
                 delivery_date_from=None, delivery_date_to=None, order_date_from=None, order_date_to=None):
        self.customer_id = customer_id
        self.seller_id = seller_id
        self.status = status
        self.delivery_date_from = delivery_date_from
        self.delivery_date_to = delivery_date_to
        self.order_date_from = order_date_from
        self.order_date_to = order_date_to
    
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
        
        # Date filters for delivery dates
        if self.delivery_date_from:
            try:
                date_from = datetime.strptime(self.delivery_date_from, '%Y-%m-%d')
                query = query.filter(Order.delivery_date >= date_from)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        if self.delivery_date_to:
            try:
                date_to = datetime.strptime(self.delivery_date_to, '%Y-%m-%d')
                query = query.filter(Order.delivery_date <= date_to)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        # Date filters for order dates
        if self.order_date_from:
            try:
                date_from = datetime.strptime(self.order_date_from, '%Y-%m-%d')
                query = query.filter(Order.order_date >= date_from)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        if self.order_date_to:
            try:
                date_to = datetime.strptime(self.order_date_to, '%Y-%m-%d')
                query = query.filter(Order.order_date <= date_to)
            except ValueError:
                pass  # Invalid date format, skip filter
        
        # Order by date (most recent first)
        query = query.order_by(Order.order_date.desc())
        
        orders = query.all()
        
        return [order.to_dict(include_items=True) for order in orders]
