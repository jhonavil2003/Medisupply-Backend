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
