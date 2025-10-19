import pytest
from src.commands.create_customer import CreateCustomer
from src.models.customer import Customer
from src.errors.errors import ValidationError


class TestCreateCustomerCommand:
    """Test cases for CreateCustomer command."""
    
    def test_create_customer_success(self, db):
        """Test successful customer creation."""
        data = {
            "document_type": "NIT",
            "document_number": "900123456-7",
            "business_name": "Hospital San Juan",
            "customer_type": "hospital",
            "contact_name": "María González",
            "contact_email": "contacto@hospitalsanjuan.com",
            "contact_phone": "+57 1 234 5678",
            "address": "Calle 45 # 12-34",
            "city": "Bogotá",
            "department": "Cundinamarca",
            "credit_limit": 50000000.00,
            "credit_days": 30
        }
        
        command = CreateCustomer(data)
        result = command.execute()
        
        assert result['document_number'] == '900123456-7'
        assert result['business_name'] == 'Hospital San Juan'
        assert result['customer_type'] == 'hospital'
        assert result['contact_name'] == 'María González'
        assert result['is_active'] is True
        
        # Verify in database
        customer = Customer.query.filter_by(document_number='900123456-7').first()
        assert customer is not None
    
    def test_create_customer_minimal_data(self, db):
        """Test customer creation with minimal required data."""
        data = {
            "document_type": "CC",
            "document_number": "12345678",
            "business_name": "Farmacia Central",
            "customer_type": "farmacia"
        }
        
        command = CreateCustomer(data)
        result = command.execute()
        
        assert result['document_number'] == '12345678'
        assert result['business_name'] == 'Farmacia Central'
        assert result['customer_type'] == 'farmacia'
        assert result['country'] == 'Colombia'
        assert result['credit_limit'] == 0.0
        assert result['credit_days'] == 0
    
    def test_create_customer_missing_required_field(self, db):
        """Test validation error for missing required field."""
        data = {
            "document_type": "NIT",
            "business_name": "Hospital Test",
            "customer_type": "hospital"
            # Missing document_number
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "document_number" in str(exc_info.value)
        assert "required" in str(exc_info.value)
    
    def test_create_customer_invalid_document_type(self, db):
        """Test validation error for invalid document type."""
        data = {
            "document_type": "INVALID",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital"
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "document_type must be one of" in str(exc_info.value)
    
    def test_create_customer_invalid_customer_type(self, db):
        """Test validation error for invalid customer type."""
        data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "invalid_type"
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "customer_type must be one of" in str(exc_info.value)
    
    def test_create_customer_short_document_number(self, db):
        """Test validation error for too short document number."""
        data = {
            "document_type": "NIT",
            "document_number": "123",  # Too short
            "business_name": "Hospital Test",
            "customer_type": "hospital"
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "document_number must be between 5 and 20 characters" in str(exc_info.value)
    
    def test_create_customer_invalid_email(self, db):
        """Test validation error for invalid email format."""
        data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "contact_email": "invalid-email"
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "Invalid email format" in str(exc_info.value)
    
    def test_create_customer_invalid_phone(self, db):
        """Test validation error for invalid phone format."""
        data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "contact_phone": "abc123"
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "Invalid phone format" in str(exc_info.value)
    
    def test_create_customer_negative_credit_limit(self, db):
        """Test validation error for negative credit limit."""
        data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "credit_limit": -1000
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "credit_limit cannot be negative" in str(exc_info.value)
    
    def test_create_customer_invalid_credit_days(self, db):
        """Test validation error for invalid credit days."""
        data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "credit_days": 400
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "credit_days must be between 0 and 365" in str(exc_info.value)
    
    def test_create_customer_duplicate_document(self, db, sample_customer):
        """Test validation error for duplicate document number."""
        data = {
            "document_type": "NIT",
            "document_number": sample_customer.document_number,
            "business_name": "Another Hospital",
            "customer_type": "hospital"
        }
        
        command = CreateCustomer(data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "already exists" in str(exc_info.value)
    
    def test_create_customer_whitespace_handling(self, db):
        """Test that whitespace is properly trimmed."""
        data = {
            "document_type": "NIT",
            "document_number": "  12345678  ",
            "business_name": "  Hospital Test  ",
            "customer_type": "hospital",
            "contact_name": "  John Doe  ",
            "contact_email": "  test@example.com  "
        }
        
        command = CreateCustomer(data)
        result = command.execute()
        
        assert result['document_number'] == '12345678'
        assert result['business_name'] == 'Hospital Test'
        assert result['contact_name'] == 'John Doe'
        assert result['contact_email'] == 'test@example.com'
    
    def test_create_customer_valid_email_formats(self, db):
        """Test various valid email formats."""
        valid_emails = [
            "test@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "123@example.org"
        ]
        
        for i, email in enumerate(valid_emails):
            data = {
                "document_type": "NIT",
                "document_number": f"1234567{i}",
                "business_name": "Hospital Test",
                "customer_type": "hospital",
                "contact_email": email
            }
            
            command = CreateCustomer(data)
            result = command.execute()
            
            assert result['contact_email'] == email
    
    def test_create_customer_valid_phone_formats(self, db):
        """Test various valid phone formats."""
        valid_phones = [
            "+57 1 234 5678",
            "3001234567",
            "+1-555-123-4567",
            "(555) 123-4567"
        ]
        
        for i, phone in enumerate(valid_phones):
            data = {
                "document_type": "NIT",
                "document_number": f"1234567{i}",
                "business_name": "Hospital Test",
                "customer_type": "hospital",
                "contact_phone": phone
            }
            
            command = CreateCustomer(data)
            result = command.execute()
            
            assert result['contact_phone'] == phone