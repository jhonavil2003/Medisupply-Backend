import pytest
import json


class TestInventoryStockLevelsEndpoint:
    
    def test_get_stock_levels_single_product(self, client, multiple_inventory_items):
        response = client.get('/inventory/stock-levels?product_sku=JER-001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['product_sku'] == 'JER-001'
        assert data['total_available'] == 150
    
    def test_get_stock_levels_multiple_products(self, client, multiple_inventory_items):
        response = client.get('/inventory/stock-levels?product_skus=JER-001,VAC-001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_products'] == 2
    
    def test_get_stock_levels_by_center(self, client, multiple_inventory_items, sample_distribution_center):
        response = client.get(f'/inventory/stock-levels?product_sku=JER-001&distribution_center_id={sample_distribution_center.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['distribution_centers']) == 1
    
    def test_get_stock_levels_only_available(self, client, multiple_inventory_items):
        response = client.get('/inventory/stock-levels?product_skus=JER-001,GUANTE-001&only_available=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_products'] == 1
    
    def test_get_stock_levels_without_parameters(self, client):
        response = client.get('/inventory/stock-levels')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_stock_levels_conflicting_parameters(self, client):
        response = client.get('/inventory/stock-levels?product_sku=JER-001&product_skus=VAC-001')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_stock_levels_with_reserved(self, client, sample_inventory):
        response = client.get('/inventory/stock-levels?product_sku=JER-001&include_reserved=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_reserved'] == 10
    
    def test_get_stock_levels_without_reserved(self, client, sample_inventory):
        response = client.get('/inventory/stock-levels?product_sku=JER-001&include_reserved=false')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_reserved'] is None
    
    def test_get_stock_levels_with_in_transit(self, client, sample_inventory):
        response = client.get('/inventory/stock-levels?product_sku=JER-001&include_in_transit=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_in_transit'] == 5


class TestHealthCheckEndpoint:
    
    def test_health_check(self, client):
        response = client.get('/inventory/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'logistics-service'

    class TestInventoryCreateAndUpdate:
        def test_create_inventory_missing_body(self, client):
            response = client.post('/inventory', data=None)
            assert response.status_code in (400, 415, 500)
            data = json.loads(response.data)
            error_msg = data.get('error', '')
            assert (
                'body' in error_msg or
                'Request body is required' in error_msg or
                'Unsupported Media Type' in error_msg
            )

        def test_create_inventory_missing_fields(self, client):
            response = client.post('/inventory', json={})
            assert response.status_code in (400, 500)
            data = json.loads(response.data)
            assert (
                'body' in data.get('error', '') or
                'product_sku is required' in data.get('error', '') or
                'distribution_center_id is required' in data.get('error', '')
            )

        def test_create_inventory_duplicate(self, client, sample_inventory):
            # sample_inventory fixture creates an inventory for JER-001 in center 1
            payload = {
                "product_sku": "JER-001",
                "distribution_center_id": 1,
                "quantity_available": 100
            }
            response = client.post('/inventory', json=payload)
            assert response.status_code == 400 or response.status_code == 409
            data = json.loads(response.data)
            assert 'already exists' in data.get('error', '')

        def test_update_inventory_missing_body(self, client):
            response = client.put('/inventory/JER-001/update', data=None)
            assert response.status_code in (400, 415, 500)
            data = json.loads(response.data)
            error_msg = data.get('error', '')
            assert (
                'body' in error_msg or
                'Se requiere el body' in error_msg or
                'Unsupported Media Type' in error_msg
            )

        def test_update_inventory_no_fields(self, client):
            response = client.put('/inventory/JER-001/update', json={"distribution_center_id": 1})
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'al menos uno' in data.get('error', '')

        def test_update_inventory_not_found(self, client):
            response = client.put('/inventory/NOEXISTE/update', json={"distribution_center_id": 1, "quantity_available": 10})
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'No se encontró inventario' in data.get('error', '')

        def test_update_inventory_trigger_websocket_false(self, client, sample_inventory):
            payload = {
                "distribution_center_id": 1,
                "quantity_available": 99,
                "trigger_websocket": False
            }
            response = client.put('/inventory/JER-001/update', json=payload)
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data']['websocket_notification_sent'] is False
