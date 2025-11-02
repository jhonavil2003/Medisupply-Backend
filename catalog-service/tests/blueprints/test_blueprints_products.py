import pytest
import json


class TestProductsListEndpoint:
    
    def test_list_products_success(self, client, multiple_products):
        response = client.get('/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert len(data['products']) == 3
    
    def test_list_products_with_search(self, client, multiple_products):
        response = client.get('/products?search=jeringa')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
    
    def test_list_products_with_category_filter(self, client, multiple_products):
        response = client.get('/products?category=Instrumental')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
    
    def test_list_products_with_subcategory_filter(self, client, multiple_products):
        response = client.get('/products?subcategory=Vacunas')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
    
    def test_list_products_with_supplier_filter(self, client, multiple_products, sample_supplier):
        response = client.get(f'/products?supplier_id={sample_supplier.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 3
    
    def test_list_products_with_is_active_true(self, client, multiple_products):
        response = client.get('/products?is_active=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 3
    
    def test_list_products_with_cold_chain_true(self, client, multiple_products):
        response = client.get('/products?requires_cold_chain=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
    
    def test_list_products_with_pagination(self, client, multiple_products):
        response = client.get('/products?page=1&per_page=2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 2
        assert data['pagination']['page'] == 1
    
    def test_list_products_page_2(self, client, multiple_products):
        response = client.get('/products?page=2&per_page=2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
    
    def test_list_products_invalid_page_zero(self, client, multiple_products):
        response = client.get('/products?page=0')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_list_products_invalid_per_page_zero(self, client, multiple_products):
        response = client.get('/products?per_page=0')
        
        assert response.status_code == 400
    
    def test_list_products_combined_filters(self, client, multiple_products):
        response = client.get('/products?category=Medicamentos&requires_cold_chain=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 1
    
    def test_list_products_no_results(self, client, multiple_products):
        response = client.get('/products?search=nonexistent')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) == 0


class TestProductDetailEndpoint:
    
    def test_get_product_by_id_success(self, client, sample_product):
        # sample_product debe tener un ID, usualmente 1 en las pruebas
        response = client.get(f'/products/{sample_product.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_product.id
        assert data['sku'] == sample_product.sku
    
    def test_get_product_by_id_not_found(self, client):
        response = client.get('/products/99999')  # ID que no existe
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
