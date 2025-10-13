from src.models.customer import Customer
from src.session import db


class GetCustomers:
    """Command to get list of customers with optional filtering."""
    
    def __init__(self, customer_type=None, city=None, is_active=None):
        self.customer_type = customer_type
        self.city = city
        self.is_active = is_active
    
    def execute(self):
        """
        Execute the command to retrieve customers.
        
        Returns:
            list: List of customer dictionaries
        """
        query = Customer.query
        
        # Apply filters
        if self.customer_type:
            query = query.filter(Customer.customer_type == self.customer_type)
        
        if self.city:
            query = query.filter(Customer.city.ilike(f'%{self.city}%'))
        
        if self.is_active is not None:
            query = query.filter(Customer.is_active == self.is_active)
        
        # Order by business name
        query = query.order_by(Customer.business_name)
        
        customers = query.all()
        
        return [customer.to_dict() for customer in customers]
