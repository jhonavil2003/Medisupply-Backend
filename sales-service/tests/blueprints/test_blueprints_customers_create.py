import pytest
import json
from src.models.customer import Customer


class TestCreateCustomer:
    """Test cases for POST /customers endpoint."""
    
    def test_create_customer_success(self, client, db):
        """Test successful customer creation."""
        customer_data = {
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
        
        response = client.post('/customers', 
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['message'] == 'Customer created successfully'
        assert 'customer' in data
        assert data['customer']['document_number'] == '900123456-7'
        assert data['customer']['business_name'] == 'Hospital San Juan'
        assert data['customer']['customer_type'] == 'hospital'
        assert data['customer']['is_active'] is True
        
        # Verify customer was saved in database
        customer = Customer.query.filter_by(document_number='900123456-7').first()
        assert customer is not None
        assert customer.business_name == 'Hospital San Juan'
    
    def test_create_customer_minimal_data(self, client, db):
        """Test customer creation with minimal required data."""
        customer_data = {
            "document_type": "CC",
            "document_number": "12345678",
            "business_name": "Farmacia Central",
            "customer_type": "farmacia"
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['customer']['document_number'] == '12345678'
        assert data['customer']['business_name'] == 'Farmacia Central'
        assert data['customer']['customer_type'] == 'farmacia'
        assert data['customer']['country'] == 'Colombia'  # Default value
        assert data['customer']['credit_limit'] == 0.0  # Default value
        assert data['customer']['credit_days'] == 0  # Default value
    
    def test_create_customer_missing_required_field(self, client, db):
        """Test customer creation with missing required field."""
        customer_data = {
            "document_type": "NIT",
            "business_name": "Hospital Test",
            "customer_type": "hospital"
            # Missing document_number
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'document_number' in data['error']
        assert 'required' in data['error']
    
    def test_create_customer_invalid_document_type(self, client, db):
        """Test customer creation with invalid document type."""
        customer_data = {
            "document_type": "INVALID",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital"
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'document_type must be one of' in data['error']
    
    def test_create_customer_invalid_customer_type(self, client, db):
        """Test customer creation with invalid customer type."""
        customer_data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "invalid_type"
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'customer_type must be one of' in data['error']
    
    def test_create_customer_invalid_email(self, client, db):
        """Test customer creation with invalid email format."""
        customer_data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "contact_email": "invalid-email"
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid email format' in data['error']
    
    def test_create_customer_duplicate_document(self, client, db, sample_customer):
        """Test customer creation with duplicate document number."""
        customer_data = {
            "document_type": "NIT",
            "document_number": sample_customer.document_number,  # Same as existing customer
            "business_name": "Another Hospital",
            "customer_type": "hospital"
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'already exists' in data['error']
    
    def test_create_customer_invalid_credit_limit(self, client, db):
        """Test customer creation with invalid credit limit."""
        customer_data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "credit_limit": -1000  # Negative value
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'credit_limit cannot be negative' in data['error']
    
    def test_create_customer_invalid_credit_days(self, client, db):
        """Test customer creation with invalid credit days."""
        customer_data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "credit_days": 400  # Too many days
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'credit_days must be between 0 and 365' in data['error']
    
    def test_create_customer_no_json_data(self, client, db):
        """Test customer creation with empty JSON data."""
        response = client.post('/customers',
                             data='{}',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        # When empty JSON is sent, it should fail validation for missing required fields
    
    def test_create_customer_invalid_phone(self, client, db):
        """Test customer creation with invalid phone format."""
        customer_data = {
            "document_type": "NIT",
            "document_number": "12345678",
            "business_name": "Hospital Test",
            "customer_type": "hospital",
            "contact_phone": "abc123"  # Invalid format
        }
        
        response = client.post('/customers',
                             data=json.dumps(customer_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'Invalid phone format' in data['error']