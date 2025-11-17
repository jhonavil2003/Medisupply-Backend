from src.models.customer import Customer
from src.entities.salesperson import Salesperson
from src.session import db
from src.errors.errors import ValidationError, NotFoundError


class AssignSalespersonToCustomer:
    """Command to assign or update a salesperson for a customer."""
    
    def __init__(self, customer_id, salesperson_id):
        """
        Initialize the command.
        
        Args:
            customer_id (int): Customer ID
            salesperson_id (int or None): Salesperson ID to assign, or None to unassign
        """
        self.customer_id = customer_id
        self.salesperson_id = salesperson_id
    
    def execute(self):
        """
        Execute the command to assign/unassign salesperson.
        
        Returns:
            dict: Updated customer data
            
        Raises:
            NotFoundError: If customer or salesperson not found
            ValidationError: If validation fails
        """
        # Validate customer exists
        customer = self._get_customer()
        
        # Validate salesperson if provided
        if self.salesperson_id is not None:
            salesperson = self._validate_salesperson()
            customer.salesperson_id = salesperson.id
        else:
            # Unassign salesperson
            customer.salesperson_id = None
        
        # Save changes
        db.session.commit()
        
        return customer.to_dict()
    
    def _get_customer(self):
        """Get and validate customer exists."""
        customer = Customer.query.get(self.customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {self.customer_id} not found")
        return customer
    
    def _validate_salesperson(self):
        """Validate salesperson exists and is active."""
        salesperson = Salesperson.query.get(self.salesperson_id)
        if not salesperson:
            raise NotFoundError(f"Salesperson with ID {self.salesperson_id} not found")
        
        if not salesperson.is_active:
            raise ValidationError(f"Salesperson '{salesperson.get_full_name()}' is not active")
        
        return salesperson
