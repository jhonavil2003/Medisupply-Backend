import pytest
import json
from datetime import date, timedelta
from src.models.product_batch import ProductBatch


class TestProductLocationEndpoint:
    """Tests para el endpoint /inventory/product-location"""
    
    def test_get_product_location_by_sku_success(self, client, db, warehouse_location):
        """Verifica búsqueda exitosa por SKU"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            barcode='7501234567890',
            is_available=True
        )
        db.session.add(batch)
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['found'] is True
        assert data['total_locations'] == 1
        assert data['total_quantity'] == 100
    
    def test_get_product_location_by_barcode(self, client, db, warehouse_location):
        """Verifica búsqueda por código de barras"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            barcode='7501234567890',
            is_available=True
        )
        db.session.add(batch)
        db.session.commit()
        
        response = client.get('/inventory/product-location?barcode=7501234567890')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['found'] is True
        assert data['locations'][0]['batch']['batch_info']['barcode'] == '7501234567890'
    
    def test_get_product_location_with_search_term(self, client, db, warehouse_location):
        """Verifica búsqueda con término general"""
        batch = ProductBatch(
            product_sku='GUANTE-LATEX-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        db.session.add(batch)
        db.session.commit()
        
        response = client.get('/inventory/product-location?search_term=GUANTE')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['found'] is True
    
    def test_get_product_location_fefo_ordering(self, client, db, warehouse_location):
        """Verifica ordenamiento FEFO"""
        batch1 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        batch2 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=30),
            is_available=True
        )
        db.session.add_all([batch1, batch2])
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001&order_by=fefo')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_locations'] == 2
        # El primero debe ser el que vence más pronto
        assert data['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-002'
    
    def test_get_product_location_filter_by_zone(self, client, db, warehouse_location, warehouse_location_ambient):
        """Verifica filtrado por tipo de zona"""
        batch_cold = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        batch_ambient = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location_ambient.distribution_center_id,
            location_id=warehouse_location_ambient.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        db.session.add_all([batch_cold, batch_ambient])
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001&zone_type=refrigerated')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_locations'] == 1
        assert data['locations'][0]['physical_location']['zone_type'] == 'refrigerated'
    
    def test_get_product_location_filter_by_expiry_range(self, client, db, warehouse_location):
        """Verifica filtrado por rango de fechas"""
        batch1 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=30),
            is_available=True
        )
        batch2 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        db.session.add_all([batch1, batch2])
        db.session.commit()
        
        expiry_from = date.today().isoformat()
        expiry_to = (date.today() + timedelta(days=60)).isoformat()
        
        response = client.get(
            f'/inventory/product-location?product_sku=TEST-001&expiry_date_from={expiry_from}&expiry_date_to={expiry_to}'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_locations'] == 1
        assert data['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-001'
    
    def test_get_product_location_no_search_param_error(self, client):
        """Verifica error cuando no se proporciona parámetro de búsqueda"""
        response = client.get('/inventory/product-location')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_product_location_invalid_zone_type(self, client):
        """Verifica error con tipo de zona inválido"""
        response = client.get('/inventory/product-location?product_sku=TEST-001&zone_type=invalid')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_product_location_not_found(self, client, db):
        """Verifica respuesta cuando no se encuentra el producto"""
        response = client.get('/inventory/product-location?product_sku=NONEXISTENT')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_product_location_include_temperature_info(self, client, db, warehouse_location):
        """Verifica que se incluye información de temperatura"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            required_temperature_min=2.0,
            required_temperature_max=8.0,
            is_available=True
        )
        db.session.add(batch)
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'temperature_status' in data['locations'][0]
        temp_status = data['locations'][0]['temperature_status']
        assert temp_status['required_range'] == '2.0°C - 8.0°C'
    
    def test_get_product_location_exclude_expired_default(self, client, db, warehouse_location):
        """Verifica que por defecto se excluyen lotes vencidos"""
        batch_expired = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() - timedelta(days=10),
            is_available=True
        )
        batch_valid = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=90),
            is_available=True
        )
        db.session.add_all([batch_expired, batch_valid])
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_locations'] == 1
        assert data['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-002'
    
    def test_get_product_location_include_expired(self, client, db, warehouse_location):
        """Verifica inclusión de lotes vencidos cuando se solicita"""
        batch_expired = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() - timedelta(days=10),
            is_available=True
        )
        batch_valid = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=90),
            is_available=True
        )
        db.session.add_all([batch_expired, batch_valid])
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001&include_expired=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_locations'] == 2
    
    def test_get_product_location_response_structure(self, client, db, warehouse_location):
        """Verifica la estructura completa de la respuesta"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            barcode='7501234567890',
            is_available=True
        )
        db.session.add(batch)
        db.session.commit()
        
        response = client.get('/inventory/product-location?product_sku=TEST-001')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estructura principal
        assert 'found' in data
        assert 'product_skus' in data
        assert 'total_locations' in data
        assert 'total_quantity' in data
        assert 'locations' in data
        assert 'ordering' in data
        assert 'search_criteria' in data
        assert 'timestamp' in data
        
        # Verificar estructura de location
        location = data['locations'][0]
        assert 'batch' in location
        assert 'physical_location' in location
        assert 'distribution_center' in location
        
        # Verificar estructura de batch
        assert 'batch_info' in location['batch']
        assert 'dates' in location['batch']
        assert 'temperature_requirements' in location['batch']
        assert 'status' in location['batch']
        
        # Verificar estructura de physical_location
        assert 'aisle' in location['physical_location']
        assert 'shelf' in location['physical_location']
        assert 'level_position' in location['physical_location']
        assert 'location_code' in location['physical_location']
        assert 'zone_type' in location['physical_location']
