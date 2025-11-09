from datetime import datetime
from sqlalchemy.orm import joinedload
from src.models.order import Order


class GetOrders:
    """Command to get list of orders with optional filtering and pagination."""
    
    def __init__(self, customer_id=None, seller_id=None, status=None, 
                 delivery_date_from=None, delivery_date_to=None, order_date_from=None, order_date_to=None,
                 page=1, per_page=20, include_details=False):
        self.customer_id = customer_id
        self.seller_id = seller_id
        self.status = status
        self.delivery_date_from = delivery_date_from
        self.delivery_date_to = delivery_date_to
        self.order_date_from = order_date_from
        self.order_date_to = order_date_to
        self.page = max(1, page)  # Asegurar que page sea al menos 1
        self.per_page = min(max(1, per_page), 100)  # Limitar entre 1 y 100
        self.include_details = include_details
    
    def execute(self):
        """
        Execute the command to retrieve orders.
        
        Returns:
            dict: Dictionary containing orders list, pagination info and total count
        """
        # Eager load customer relationship to avoid N+1 queries
        query = Order.query.options(joinedload(Order.customer))
        
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
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        offset = (self.page - 1) * self.per_page
        orders = query.limit(self.per_page).offset(offset).all()
        
        # Return data based on include_details flag
        # Para listados móviles: solo datos resumidos (sin items)
        # Para detalles o exportación: datos completos
        if self.include_details:
            orders_data = [order.to_dict(include_items=True, include_customer=True) for order in orders]
        else:
            # Datos resumidos para listado móvil
            orders_data = [order.to_dict(include_items=False, include_customer=True) for order in orders]
        
        return {
            'orders': orders_data,
            'total': total,
            'page': self.page,
            'per_page': self.per_page,
            'total_pages': (total + self.per_page - 1) // self.per_page if self.per_page > 0 else 0
        }
