import json
import pytest
from decimal import Decimal
from src.models.product import Product
from src.models.supplier import Supplier


class TestProductsBlueprint:
    """Test suite for products blueprint endpoints"""

    def test_list_products_success(self, client, sample_product):
        """Test GET /products returns products list"""
        response = client.get('/products')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'products' in data
        assert 'pagination' in data
        assert len(data['products']) > 0
        assert data['products'][0]['sku'] == 'TEST-001'

    def test_list_products_with_search(self, client, sample_product):
        """Test GET /products with search parameter"""
        response = client.get('/products?search=Test Product')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) > 0
        assert 'Test Product' in data['products'][0]['name']

    def test_list_products_with_filters(self, client, sample_product):
        """Test GET /products with various filters"""
        response = client.get('/products?category=Medical Equipment&is_active=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) > 0

    def test_list_products_pagination(self, client, multiple_products):
        """Test GET /products with pagination"""
        response = client.get('/products?page=1&per_page=2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['products']) <= 2
        assert 'pagination' in data

    def test_list_products_invalid_pagination(self, client):
        """Test GET /products with invalid pagination parameters"""
        response = client.get('/products?page=0')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_product_success(self, client, sample_supplier):
        """Test POST /products creates new product"""
        product_data = {
            'sku': 'NEW-001',
            'name': 'New Test Product',
            'category': 'Test Category',
            'unit_price': 99.99,
            'unit_of_measure': 'unit',
            'supplier_id': sample_supplier.id,
            'description': 'New product description'
        }
        
        response = client.post('/products', 
                             data=json.dumps(product_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['sku'] == 'NEW-001'
        assert data['name'] == 'New Test Product'

    def test_create_product_missing_required_fields(self, client):
        """Test POST /products with missing required fields"""
        product_data = {
            'name': 'Incomplete Product'
        }
        
        response = client.post('/products',
                             data=json.dumps(product_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_product_duplicate_sku(self, client, sample_product, sample_supplier):
        """Test POST /products with duplicate SKU"""
        product_data = {
            'sku': 'TEST-001',  # Same as sample_product
            'name': 'Duplicate SKU Product',
            'category': 'Test Category',
            'unit_price': 99.99,
            'unit_of_measure': 'unit',
            'supplier_id': sample_supplier.id
        }
        
        response = client.post('/products',
                             data=json.dumps(product_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['error']

    def test_create_product_no_request_body(self, client):
        """Test POST /products without request body"""
        response = client.post('/products')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Request body is required' in data['error']

    def test_get_product_by_id_success(self, client, sample_product):
        """Test GET /products/<id> returns specific product"""
        response = client.get(f'/products/{sample_product.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_product.id
        assert data['sku'] == 'TEST-001'
        assert data['name'] == 'Test Product'

    def test_get_product_by_id_not_found(self, client):
        """Test GET /products/<id> with non-existent ID"""
        response = client.get('/products/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()

    def test_get_product_by_id_invalid_id(self, client):
        """Test GET /products/<id> with invalid ID format"""
        response = client.get('/products/invalid')
        
        assert response.status_code == 404  # Flask returns 404 for invalid route params

    def test_update_product_success(self, client, sample_product):
        """Test PUT /products/<id> updates product"""
        update_data = {
            'name': 'Updated Product Name',
            'description': 'Updated description',
            'unit_price': 149.99
        }
        
        response = client.put(f'/products/{sample_product.id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Product Name'
        assert data['description'] == 'Updated description'
        assert float(data['unit_price']) == 149.99

    def test_update_product_not_found(self, client):
        """Test PUT /products/<id> with non-existent ID"""
        update_data = {'name': 'Updated Name'}
        
        response = client.put('/products/99999',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()

    def test_update_product_no_request_body(self, client, sample_product):
        """Test PUT /products/<id> without request body"""
        response = client.put(f'/products/{sample_product.id}')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Request body is required' in data['error']

    def test_update_product_sku_ignored(self, client, sample_product):
        """Test PUT /products/<id> ignores SKU updates"""
        original_sku = sample_product.sku
        update_data = {
            'sku': 'NEW-SKU',
            'name': 'Updated Product'
        }
        
        response = client.put(f'/products/{sample_product.id}',
                            data=json.dumps(update_data),
                            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['sku'] == original_sku  # SKU should not change

    def test_delete_product_soft_delete(self, client, sample_product):
        """Test DELETE /products/<id> performs soft delete"""
        response = client.delete(f'/products/{sample_product.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deleted' in data['message'].lower() or 'deactivated' in data['message'].lower()

    def test_delete_product_hard_delete(self, client, sample_product):
        """Test DELETE /products/<id> with hard_delete=true"""
        response = client.delete(f'/products/{sample_product.id}?hard_delete=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'deleted' in data['message'].lower()

    def test_delete_product_not_found(self, client):
        """Test DELETE /products/<id> with non-existent ID"""
        response = client.delete('/products/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()

    def test_health_check(self, client):
        """Test GET /products/health endpoint"""
        response = client.get('/products/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'catalog-service'

    def test_products_blueprint_error_handling(self, client, mocker):
        """Test error handling in products blueprint"""
        # Mock GetProducts to raise an exception
        mocker.patch('src.commands.get_products.GetProducts.execute',
                    side_effect=Exception('Database error'))
        
        response = client.get('/products')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_product_validation_error_handling(self, client):
        """Test validation error handling in create product"""
        product_data = {
            'sku': 'TEST-002',
            'name': 'Test Product',
            'category': 'Test',
            'unit_price': -10,  # Invalid negative price
            'unit_of_measure': 'unit',
            'supplier_id': 999  # Non-existent supplier
        }
        
        response = client.post('/products',
                             data=json.dumps(product_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data