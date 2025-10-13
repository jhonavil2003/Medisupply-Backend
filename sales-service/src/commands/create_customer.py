from src.models.customer import Customer
from src.session import db
from src.errors.errors import ValidationError
import re


class CreateCustomer:
    """Command to create a new customer with validation."""
    
    def __init__(self, data):
        self.data = data
    
    def execute(self):
        """
        Execute the command to create a customer.
        
        Returns:
            dict: Created customer data
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        self._validate_required_fields()
        
        # Validate business rules
        self._validate_business_rules()
        
        # Check if customer already exists
        self._check_customer_exists()
        
        # Create customer
        customer = self._create_customer()
        
        return customer.to_dict()
    
    def _validate_required_fields(self):
        """Validate required fields are present."""
        required_fields = [
            'document_type',
            'document_number', 
            'business_name',
            'customer_type'
        ]
        
        for field in required_fields:
            if not self.data.get(field):
                raise ValidationError(f"Field '{field}' is required")
    
    def _validate_business_rules(self):
        """Validate business rules and data formats."""
        # Validate document_type
        valid_document_types = ['NIT', 'CC', 'CE', 'RUT', 'DNI']
        if self.data['document_type'] not in valid_document_types:
            raise ValidationError(f"document_type must be one of: {', '.join(valid_document_types)}")
        
        # Validate customer_type
        valid_customer_types = ['hospital', 'clinica', 'farmacia', 'distribuidor', 'ips', 'eps']
        if self.data['customer_type'] not in valid_customer_types:
            raise ValidationError(f"customer_type must be one of: {', '.join(valid_customer_types)}")
        
        # Validate document_number format
        document_number = self.data['document_number'].strip()
        if len(document_number) < 5 or len(document_number) > 20:
            raise ValidationError("document_number must be between 5 and 20 characters")
        
        # Validate email format if provided
        if self.data.get('contact_email'):
            email = self.data['contact_email'].strip()
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValidationError("Invalid email format")
        
        # Validate phone format if provided
        if self.data.get('contact_phone'):
            phone = self.data['contact_phone'].strip()
            phone_pattern = r'^[\+]?[\d\s\-\(\)]{7,20}$'
            if not re.match(phone_pattern, phone):
                raise ValidationError("Invalid phone format")
        
        # Validate credit_limit if provided
        if self.data.get('credit_limit') is not None:
            try:
                credit_limit = float(self.data['credit_limit'])
                if credit_limit < 0:
                    raise ValidationError("credit_limit cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("credit_limit must be a valid number")
        
        # Validate credit_days if provided
        if self.data.get('credit_days') is not None:
            try:
                credit_days = int(self.data['credit_days'])
                if credit_days < 0 or credit_days > 365:
                    raise ValidationError("credit_days must be between 0 and 365")
            except (ValueError, TypeError):
                raise ValidationError("credit_days must be a valid integer")
    
    def _check_customer_exists(self):
        """Check if customer with same document already exists."""
        existing_customer = Customer.query.filter_by(
            document_number=self.data['document_number'].strip()
        ).first()
        
        if existing_customer:
            raise ValidationError(f"Customer with document number '{self.data['document_number']}' already exists")
    
    def _create_customer(self):
        """Create the customer record."""
        customer = Customer(
            document_type=self.data['document_type'],
            document_number=self.data['document_number'].strip(),
            business_name=self.data['business_name'].strip(),
            trade_name=self.data.get('trade_name', '').strip() if self.data.get('trade_name') else None,
            customer_type=self.data['customer_type'],
            contact_name=self.data.get('contact_name', '').strip() if self.data.get('contact_name') else None,
            contact_email=self.data.get('contact_email', '').strip() if self.data.get('contact_email') else None,
            contact_phone=self.data.get('contact_phone', '').strip() if self.data.get('contact_phone') else None,
            address=self.data.get('address', '').strip() if self.data.get('address') else None,
            city=self.data.get('city', '').strip() if self.data.get('city') else None,
            department=self.data.get('department', '').strip() if self.data.get('department') else None,
            country=self.data.get('country', 'Colombia').strip(),
            credit_limit=float(self.data.get('credit_limit', 0.0)),
            credit_days=int(self.data.get('credit_days', 0)),
            is_active=bool(self.data.get('is_active', True))
        )
        
        db.session.add(customer)
        db.session.commit()
        
        return customer