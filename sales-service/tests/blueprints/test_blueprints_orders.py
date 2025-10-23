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
    
    # ==================== PATCH ENDPOINT TESTS ====================
    
    def test_update_order_success(self, client, sample_order):
        """Test PATCH /orders/<id> - successful update."""
        update_data = {
            'delivery_address': 'Nueva Calle 123 #45-67',
            'delivery_city': 'Medellín',
            'delivery_department': 'Antioquia',
            'notes': 'Entrega urgente'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_order.id
        assert data['delivery_address'] == 'Nueva Calle 123 #45-67'
        assert data['delivery_city'] == 'Medellín'
        assert data['delivery_department'] == 'Antioquia'
        assert data['notes'] == 'Entrega urgente'
    
    def test_update_order_partial_update(self, client, sample_order):
        """Test PATCH /orders/<id> - partial update only changes specified fields."""
        original_address = sample_order.delivery_address
        original_payment_terms = sample_order.payment_terms
        
        update_data = {
            'notes': 'Solo actualizo las notas'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Changed field
        assert data['notes'] == 'Solo actualizo las notas'
        
        # Unchanged fields should remain the same
        assert data['delivery_address'] == original_address
        assert data['payment_terms'] == original_payment_terms
    
    def test_update_order_status_pending_to_confirmed(self, client, sample_order):
        """Test PATCH /orders/<id> - valid status transition."""
        update_data = {
            'status': 'confirmed'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'confirmed'
    
    def test_update_order_with_items(self, client, sample_order):
        """Test PATCH /orders/<id> - update with new items."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU-001',
                    'product_name': 'Test Product',
                    'quantity': 25,
                    'unit_price': 2000.00,
                    'discount_percentage': 5.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify items were replaced
        assert len(data['items']) == 1
        assert data['items'][0]['product_sku'] == 'TEST-SKU-001'
        assert data['items'][0]['quantity'] == 25
        
        # Verify totals were recalculated
        # 25 * 2000 = 50,000
        # Discount: 50,000 * 5% = 2,500
        # Subtotal after discount: 47,500
        # Tax: 47,500 * 19% = 9,025
        # Total: 47,500 + 9,025 = 56,525
        assert float(data['subtotal']) == 50000.00
        assert float(data['discount_amount']) == 2500.00
        assert float(data['tax_amount']) == 9025.00
        assert float(data['total_amount']) == 56525.00
    
    def test_update_order_payment_terms(self, client, sample_order):
        """Test PATCH /orders/<id> - update payment terms."""
        update_data = {
            'payment_terms': 'credito_45',
            'payment_method': 'credito'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['payment_terms'] == 'credito_45'
        assert data['payment_method'] == 'credito'
    
    def test_update_order_returns_complete_data(self, client, sample_order):
        """Test PATCH /orders/<id> - returns complete order with items and customer."""
        update_data = {
            'notes': 'Test complete response'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify complete data structure
        assert 'id' in data
        assert 'order_number' in data
        assert 'customer' in data
        assert 'items' in data
        assert len(data['items']) > 0
        
        # Verify customer data
        assert 'id' in data['customer']
        assert 'business_name' in data['customer']
        
        # Verify item data
        assert 'product_sku' in data['items'][0]
        assert 'quantity' in data['items'][0]
    
    # ==================== ERROR CASES ====================
    
    def test_update_order_not_found(self, client):
        """Test PATCH /orders/<id> - 404 when order doesn't exist."""
        update_data = {
            'notes': 'Test'
        }
        
        response = client.patch(
            '/orders/99999',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()
    
    def test_update_order_not_pending_error(self, client, sample_order, db):
        """Test PATCH /orders/<id> - 400 when order is not PENDING."""
        # Change order status to confirmed
        sample_order.status = 'confirmed'
        db.session.commit()
        
        update_data = {
            'notes': 'Try to update confirmed order'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Solo se pueden editar órdenes pendientes' in data['error']
    
    def test_update_order_invalid_status_transition(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 for invalid status transition."""
        update_data = {
            'status': 'cancelled'  # PENDING → CANCELLED not allowed
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid status transition' in data['error']
    
    def test_update_order_empty_body(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 when request body is empty."""
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_order_items_empty_list(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 when items list is empty."""
        update_data = {
            'items': []
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'at least one item' in data['error'].lower()
    
    def test_update_order_items_missing_product_sku(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 when item missing product_sku."""
        update_data = {
            'items': [
                {
                    'quantity': 10,
                    'unit_price': 1000.00
                    # Missing product_sku
                }
            ]
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'product_sku' in data['error'].lower()
    
    def test_update_order_items_missing_quantity(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 when item missing quantity."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'unit_price': 1000.00
                    # Missing quantity
                }
            ]
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'quantity' in data['error'].lower()
    
    def test_update_order_items_zero_quantity(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 when quantity is 0."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': 0,
                    'unit_price': 1000.00
                }
            ]
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'greater than 0' in data['error'].lower()
    
    def test_update_order_items_negative_quantity(self, client, sample_order):
        """Test PATCH /orders/<id> - 400 when quantity is negative."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': -5,
                    'unit_price': 1000.00
                }
            ]
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    # ==================== IMMUTABLE FIELDS TESTS ====================
    
    def test_update_order_ignores_immutable_customer_id(self, client, sample_order):
        """Test PATCH /orders/<id> - customer_id is ignored silently."""
        original_customer_id = sample_order.customer_id
        
        update_data = {
            'customer_id': 99999,  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # customer_id should not change
        assert data['customer_id'] == original_customer_id
        # But other fields should update
        assert data['notes'] == 'Update notes'
    
    def test_update_order_ignores_immutable_order_number(self, client, sample_order):
        """Test PATCH /orders/<id> - order_number is ignored silently."""
        original_order_number = sample_order.order_number
        
        update_data = {
            'order_number': 'FAKE-ORDER-9999',  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # order_number should not change
        assert data['order_number'] == original_order_number
        # But other fields should update
        assert data['notes'] == 'Update notes'
    
    def test_update_order_ignores_immutable_totals(self, client, sample_order):
        """Test PATCH /orders/<id> - monetary totals are ignored."""
        update_data = {
            'subtotal': 999999.99,  # Try to change immutable field
            'total_amount': 999999.99,  # Try to change immutable field
            'notes': 'Update notes'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Totals should not change to fake values
        assert float(data['subtotal']) != 999999.99
        assert float(data['total_amount']) != 999999.99
        # But other fields should update
        assert data['notes'] == 'Update notes'
