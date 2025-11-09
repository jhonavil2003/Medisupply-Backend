import pytest
import json


class TestOrdersUpdateErrorHandling:
    """Tests for error handling in PATCH /orders/<id> endpoint."""
    
    # ==================== 400 BAD REQUEST TESTS ====================
    
    def test_update_order_invalid_content_type(self, client, sample_order):
        """Test PATCH with invalid Content-Type returns 400."""
        response = client.patch(
            f'/orders/{sample_order.id}',
            data='{"notes": "test"}',  # Plain text, not JSON
            content_type='text/plain'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'application/json' in data['error'].lower()
    
    def test_update_order_empty_json_body(self, client, sample_order):
        """Test PATCH with empty JSON body returns 400."""
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        # Message can be either about empty body or needing at least one field
        assert ('required' in data['error'].lower() or 
                'empty' in data['error'].lower() or 
                'at least one field' in data['error'].lower())
    
    def test_update_order_invalid_json_format(self, client, sample_order):
        """Test PATCH with malformed JSON returns 400 or 500."""
        response = client.patch(
            f'/orders/{sample_order.id}',
            data='{"notes": invalid}',  # Invalid JSON
            content_type='application/json'
        )
        
        # Flask handles malformed JSON at framework level, may return 400 or 500
        assert response.status_code in [400, 500]
    
    def test_update_order_invalid_status_value(self, client, sample_order):
        """Test PATCH with invalid status value returns 400."""
        update_data = {
            'status': 'invalid_status_value'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'invalid status' in data['error'].lower()
    
    def test_update_order_items_invalid_type(self, client, sample_order):
        """Test PATCH with items as non-list returns 400."""
        update_data = {
            'items': 'not-a-list'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'list' in data['error'].lower()
    
    def test_update_order_items_empty_array(self, client, sample_order):
        """Test PATCH with empty items array returns 400."""
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
    
    def test_update_order_item_missing_sku(self, client, sample_order):
        """Test PATCH with item missing product_sku returns 400."""
        update_data = {
            'items': [
                {
                    'quantity': 10,
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
        assert 'product_sku' in data['error'].lower()
        assert 'index 0' in data['error'].lower()
    
    def test_update_order_item_missing_quantity(self, client, sample_order):
        """Test PATCH with item missing quantity returns 400."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
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
        assert 'quantity' in data['error'].lower()
    
    def test_update_order_item_zero_quantity(self, client, sample_order):
        """Test PATCH with zero quantity returns 400."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': 0
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
    
    def test_update_order_item_negative_quantity(self, client, sample_order):
        """Test PATCH with negative quantity returns 400."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': -5
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
        assert ('greater than 0' in data['error'].lower() or 
                'positive' in data['error'].lower())
    
    def test_update_order_item_invalid_quantity_type(self, client, sample_order):
        """Test PATCH with non-numeric quantity returns 400."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': 'not-a-number'
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
    
    def test_update_order_item_negative_price(self, client, sample_order):
        """Test PATCH with negative unit_price returns 400."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': 10,
                    'unit_price': -100.00
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
        assert 'negative' in data['error'].lower() or 'unit_price' in data['error'].lower()
    
    def test_update_order_item_invalid_discount_percentage(self, client, sample_order):
        """Test PATCH with discount_percentage > 100 returns 400."""
        update_data = {
            'items': [
                {
                    'product_sku': 'TEST-SKU',
                    'quantity': 10,
                    'discount_percentage': 150.0
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
        assert ('discount_percentage' in data['error'].lower() or 
                'between 0 and 100' in data['error'].lower())
    
    def test_update_order_invalid_status_transition(self, client, sample_order):
        """Test PATCH with PENDING → CANCELLED transition returns 200 (now allowed)."""
        update_data = {
            'status': 'cancelled'  # PENDING → CANCELLED is allowed
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'cancelled'
    
    def test_update_order_not_pending(self, client, sample_order, db):
        """Test PATCH on confirmed order returns 200 (now allowed)."""
        # Change order to confirmed
        sample_order.status = 'confirmed'
        db.session.commit()
        
        update_data = {
            'notes': 'Try to update'
        }
        
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['notes'] == 'Try to update'
        assert data['status'] == 'confirmed'
    
    # ==================== 404 NOT FOUND TESTS ====================
    
    def test_update_order_not_found(self, client):
        """Test PATCH on non-existent order returns 404."""
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
        assert data['status_code'] == 404
    
    # ==================== ERROR RESPONSE FORMAT TESTS ====================
    
    def test_error_response_contains_status_code(self, client):
        """Test that all error responses contain status_code field."""
        response = client.patch(
            '/orders/99999',
            data=json.dumps({'notes': 'test'}),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        assert 'status_code' in data
        assert data['status_code'] == 404
    
    def test_error_response_contains_error_message(self, client, sample_order):
        """Test that all error responses contain error message."""
        response = client.patch(
            f'/orders/{sample_order.id}',
            data=json.dumps({'items': []}),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        assert 'error' in data
        assert isinstance(data['error'], str)
        assert len(data['error']) > 0
    
    def test_404_error_includes_order_id(self, client):
        """Test that 404 errors include the order_id for context."""
        order_id = 99999
        response = client.patch(
            f'/orders/{order_id}',
            data=json.dumps({'notes': 'test'}),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        assert 'order_id' in data
        assert data['order_id'] == order_id
