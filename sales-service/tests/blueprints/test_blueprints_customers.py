import pytest
import json
from decimal import Decimal


class TestCustomersBlueprint:
    
    def test_get_customers_all(self, client, sample_customer):
        """Test GET /customers without filters."""
        response = client.get('/customers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'customers' in data
        assert 'total' in data
        assert data['total'] >= 1
        assert isinstance(data['customers'], list)
    
    def test_get_customers_by_type(self, client, sample_customer):
        """Test GET /customers filtered by customer_type."""
        response = client.get('/customers?customer_type=hospital')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(cust['customer_type'] == 'hospital' for cust in data['customers'])
    
    def test_get_customers_by_city(self, client, sample_customer):
        """Test GET /customers filtered by city."""
        response = client.get(f'/customers?city={sample_customer.city}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'customers' in data
        # Verificar que si hay resultados, todos son de la ciudad correcta
        if data['total'] > 0:
            assert all(cust['city'] == sample_customer.city for cust in data['customers'])
    
    def test_get_customers_by_active_status(self, client, sample_customer):
        """Test GET /customers filtered by is_active."""
        response = client.get('/customers?is_active=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(cust['is_active'] is True for cust in data['customers'])
    
    def test_get_customers_by_active_status_false(self, client, multiple_customers):
        """Test GET /customers filtered by is_active=false."""
        response = client.get('/customers?is_active=false')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'customers' in data
        # Si hay resultados, todos deben estar inactivos
        if data['total'] > 0:
            assert all(cust['is_active'] is False for cust in data['customers'])
    
    def test_get_customers_combined_filters(self, client, sample_customer):
        """Test GET /customers with multiple filters."""
        response = client.get(f'/customers?customer_type={sample_customer.customer_type}&is_active=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'customers' in data
        if data['total'] > 0:
            assert all(
                cust['customer_type'] == sample_customer.customer_type and cust['is_active'] is True
                for cust in data['customers']
            )
    
    def test_get_customer_by_id(self, client, sample_customer):
        """Test GET /customers/<id> - retrieve single customer."""
        response = client.get(f'/customers/{sample_customer.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_customer.id
        assert data['business_name'] == sample_customer.business_name
        assert data['customer_type'] == sample_customer.customer_type
        assert 'credit_limit' in data
        assert 'is_active' in data
    
    def test_get_customer_by_id_not_found(self, client):
        """Test GET /customers/<id> with non-existent ID."""
        response = client.get('/customers/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_customers_health_check(self, client):
        """Test GET /customers/health endpoint."""
        response = client.get('/customers/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'sales-service'
        assert data['module'] == 'customers'
        assert 'version' in data
