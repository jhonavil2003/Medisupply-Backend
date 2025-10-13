from src.models.customer import Customer
from src.errors.errors import NotFoundError


class GetCustomerById:
    """Command to get a customer by ID."""
    
    def __init__(self, customer_id):
        self.customer_id = customer_id
    
    def execute(self):
        """
        Execute the command to retrieve a customer.
        
        Returns:
            dict: Customer dictionary
            
        Raises:
            NotFoundError: If customer not found
        """
        customer = Customer.query.filter_by(id=self.customer_id).first()
        
        if not customer:
            raise NotFoundError(f"Customer with ID {self.customer_id} not found")
        
        return customer.to_dict()
