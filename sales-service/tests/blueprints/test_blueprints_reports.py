"""
Tests for reports blueprints.
"""
import pytest
from datetime import datetime, timedelta
from src.models.order import Order
from src.models.order_item import OrderItem
from src.models.customer import Customer
from src.entities.salesperson import Salesperson
from src.entities.salesperson_goal import SalespersonGoal


class TestReportsBlueprint:
    """Test suite for reports blueprint endpoints."""
    
    def test_sales_summary_invalid_month(self, client):
        """Test validation error with invalid month."""
        response = client.get('/reports/sales-summary?month=invalid')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert 'error' in data
        assert 'Month must be a valid integer' in data['error']
    
    def test_sales_summary_invalid_year(self, client):
        """Test validation error with invalid year."""
        response = client.get('/reports/sales-summary?year=invalid')
        
        assert response.status_code == 400
        data = response.get_json()
        
        assert 'error' in data
        assert 'Year must be a valid integer' in data['error']
    
    def test_reports_health_check(self, client):
        """Test reports health check endpoint."""
        response = client.get('/reports/health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['service'] == 'reports'
        assert data['status'] == 'healthy'
        assert 'endpoints' in data
        assert len(data['endpoints']) >= 3
    
    def test_sales_summary_empty_result(self, client):
        """Test getting sales summary with no data."""
        response = client.get('/reports/sales-summary')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'summary' in data
        assert 'totals' in data
        assert 'filters_applied' in data
        assert 'total_records' in data
        assert isinstance(data['summary'], list)
    
    def test_sales_by_salesperson_empty_result(self, client):
        """Test getting sales by salesperson with no data."""
        response = client.get('/reports/sales-by-salesperson')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'salespersons' in data
        assert 'total_salespersons' in data
        assert 'filters_applied' in data
    
    def test_sales_by_product_empty_result(self, client):
        """Test getting sales by product with no data."""
        response = client.get('/reports/sales-by-product')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert 'products' in data
        assert 'total_products' in data
        assert 'filters_applied' in data
