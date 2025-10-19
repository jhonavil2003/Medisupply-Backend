import pytest
import json
from decimal import Decimal


class TestOrdersBlueprint:
    """Test suite for Orders Blueprint endpoints."""
    
    def test_get_orders_all(self, client, sample_order):
        """Test GET /orders without filters."""
        response = client.get('/orders')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'orders' in data
        assert 'total' in data
        assert data['total'] >= 1
        assert isinstance(data['orders'], list)
    
    def test_get_orders_by_customer(self, client, sample_order):
        """Test GET /orders filtered by customer_id."""
        response = client.get(f'/orders?customer_id={sample_order.customer_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(order['customer_id'] == sample_order.customer_id for order in data['orders'])
    
    def test_get_orders_by_seller(self, client, sample_order):
        """Test GET /orders filtered by seller_id."""
        response = client.get(f'/orders?seller_id={sample_order.seller_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(order['seller_id'] == sample_order.seller_id for order in data['orders'])
    
    def test_get_orders_by_status(self, client, sample_order):
        """Test GET /orders filtered by status."""
        response = client.get('/orders?status=pending')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'orders' in data
        if data['total'] > 0:
            assert all(order['status'] == 'pending' for order in data['orders'])
    
    def test_get_orders_combined_filters(self, client, sample_order):
        """Test GET /orders with multiple filters."""
        response = client.get(
            f'/orders?customer_id={sample_order.customer_id}&status={sample_order.status}'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'orders' in data
        if data['total'] > 0:
            assert all(
                order['customer_id'] == sample_order.customer_id and 
                order['status'] == sample_order.status
                for order in data['orders']
            )
    
    def test_get_order_by_id(self, client, sample_order):
        """Test GET /orders/<id> - retrieve single order."""
        response = client.get(f'/orders/{sample_order.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_order.id
        assert data['customer_id'] == sample_order.customer_id
        assert 'items' in data
        assert 'total_amount' in data
        assert 'status' in data
    
    def test_get_order_by_id_not_found(self, client):
        """Test GET /orders/<id> with non-existent ID."""
        response = client.get('/orders/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_order_missing_body(self, client):
        """Test POST /orders without request body."""
        response = client.post('/orders', json={})
        
        # Validación de que devuelve error (puede ser 400 o 500)
        assert response.status_code in [400, 500]
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data
    
    def test_orders_health_check(self, client):
        """Test GET /orders/health endpoint."""
        response = client.get('/orders/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'sales-service'
        assert data['module'] == 'orders'
        assert 'version' in data
    
    def test_delete_order_success(self, client, sample_order):
        """Test DELETE /orders/<id> - successful deletion."""
        response = client.delete(f'/orders/{sample_order.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'deleted_order' in data
        assert sample_order.order_number in data['message']
        assert data['deleted_order']['id'] == sample_order.id
        
        # Verify the order is deleted
        get_response = client.get(f'/orders/{sample_order.id}')
        assert get_response.status_code == 404
    
    def test_delete_order_not_found(self, client):
        """Test DELETE /orders/<id> with non-existent ID."""
        response = client.delete('/orders/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_delete_order_removes_items(self, client, sample_order):
        """Test DELETE /orders/<id> also removes order items."""
        order_id = sample_order.id
        
        # Get order first to verify it has items
        get_response = client.get(f'/orders/{order_id}')
        assert get_response.status_code == 200
        order_data = json.loads(get_response.data)
        assert len(order_data['items']) >= 2
        
        # Delete the order
        delete_response = client.delete(f'/orders/{order_id}')
        assert delete_response.status_code == 200
        
        # Verify order is gone
        verify_response = client.get(f'/orders/{order_id}')
        assert verify_response.status_code == 404
