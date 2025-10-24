import pytest
from datetime import datetime, date, timedelta
from src.models.warehouse_location import WarehouseLocation
from src.models.product_batch import ProductBatch
from src.models.distribution_center import DistributionCenter


class TestWarehouseLocation:
    """Tests para el modelo WarehouseLocation"""
    
    def test_create_warehouse_location(self, db_session, distribution_center):
        """Verifica que se puede crear una ubicación de bodega correctamente"""
        location = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='refrigerated',
            aisle='A',
            shelf='E1',
            level_position='N3-P2',
            temperature_min=2.0,
            temperature_max=8.0,
            current_temperature=5.0,
            capacity_units=100,
            is_active=True
        )
        
        db_session.add(location)
        db_session.commit()
        
        assert location.id is not None
        assert location.distribution_center_id == distribution_center.id
        assert location.zone_type == 'refrigerated'
        assert location.aisle == 'A'
        assert location.shelf == 'E1'
        assert location.level_position == 'N3-P2'
        assert location.is_active is True
    
    def test_warehouse_location_unique_constraint(self, db_session, distribution_center):
        """Verifica que no se pueden crear ubicaciones duplicadas"""
        location1 = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='ambient',
            aisle='B',
            shelf='E2',
            level_position='N1-P1'
        )
        db_session.add(location1)
        db_session.commit()
        
        # Intentar crear ubicación duplicada
        location2 = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='ambient',
            aisle='B',
            shelf='E2',
            level_position='N1-P1'
        )
        db_session.add(location2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_location_code_property(self, db_session, distribution_center):
        """Verifica que el código de ubicación se genera correctamente"""
        location = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='ambient',
            aisle='C',
            shelf='E5',
            level_position='L2'
        )
        
        assert location.location_code == 'C-E5-L2'
    
    def test_is_refrigerated_property(self, db_session, distribution_center):
        """Verifica la propiedad is_refrigerated"""
        location_cold = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='refrigerated',
            aisle='A',
            shelf='E1',
            level_position='N1'
        )
        
        location_ambient = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='ambient',
            aisle='B',
            shelf='E2',
            level_position='N1'
        )
        
        assert location_cold.is_refrigerated is True
        assert location_ambient.is_refrigerated is False
    
    def test_temperature_in_range_property(self, db_session, distribution_center):
        """Verifica la validación de temperatura"""
        location = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='refrigerated',
            aisle='A',
            shelf='E1',
            level_position='N1',
            temperature_min=2.0,
            temperature_max=8.0,
            current_temperature=5.0
        )
        
        assert location.temperature_in_range is True
        
        # Temperatura fuera de rango (muy baja)
        location.current_temperature = 1.0
        assert location.temperature_in_range is False
        
        # Temperatura fuera de rango (muy alta)
        location.current_temperature = 10.0
        assert location.temperature_in_range is False
        
        # Temperatura en rango límite
        location.current_temperature = 2.0
        assert location.temperature_in_range is True
    
    def test_warehouse_location_to_dict(self, db_session, distribution_center):
        """Verifica la serialización a diccionario"""
        location = WarehouseLocation(
            distribution_center_id=distribution_center.id,
            zone_type='refrigerated',
            aisle='A',
            shelf='E1',
            level_position='N3',
            temperature_min=2.0,
            temperature_max=8.0,
            current_temperature=5.0,
            capacity_units=50,
            is_active=True,
            notes='Ubicación para vacunas'
        )
        db_session.add(location)
        db_session.commit()
        
        location_dict = location.to_dict()
        
        assert location_dict['id'] == location.id
        assert location_dict['distribution_center_id'] == distribution_center.id
        assert location_dict['zone_type'] == 'refrigerated'
        assert location_dict['is_refrigerated'] is True
        assert location_dict['location']['aisle'] == 'A'
        assert location_dict['location']['shelf'] == 'E1'
        assert location_dict['location']['level_position'] == 'N3'
        assert location_dict['location']['code'] == 'A-E1-N3'
        assert location_dict['capacity_units'] == 50
        assert location_dict['is_active'] is True
        assert location_dict['notes'] == 'Ubicación para vacunas'
        assert 'temperature' in location_dict
        assert location_dict['temperature']['min'] == 2.0
        assert location_dict['temperature']['max'] == 8.0
        assert location_dict['temperature']['current'] == 5.0
        assert location_dict['temperature']['in_range'] is True


class TestProductBatch:
    """Tests para el modelo ProductBatch"""
    
    def test_create_product_batch(self, db_session, distribution_center, warehouse_location):
        """Verifica que se puede crear un lote de producto correctamente"""
        expiry_date = date.today() + timedelta(days=180)
        manufactured_date = date.today() - timedelta(days=90)
        
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=expiry_date,
            manufactured_date=manufactured_date,
            required_temperature_min=2.0,
            required_temperature_max=8.0,
            barcode='7501234567890',
            is_available=True
        )
        
        db_session.add(batch)
        db_session.commit()
        
        assert batch.id is not None
        assert batch.product_sku == 'TEST-001'
        assert batch.batch_number == 'BATCH-001'
        assert batch.quantity == 100
        assert batch.expiry_date == expiry_date
        assert batch.is_available is True
    
    def test_product_batch_unique_constraint(self, db_session, distribution_center, warehouse_location):
        """Verifica que no se pueden crear lotes duplicados"""
        batch1 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180)
        )
        db_session.add(batch1)
        db_session.commit()
        
        # Intentar crear lote duplicado
        batch2 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=50,
            expiry_date=date.today() + timedelta(days=180)
        )
        db_session.add(batch2)
        
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()
    
    def test_days_until_expiry(self, db_session, distribution_center, warehouse_location):
        """Verifica el cálculo de días hasta el vencimiento"""
        expiry_date = date.today() + timedelta(days=90)
        
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=expiry_date
        )
        
        assert batch.days_until_expiry == 90
    
    def test_is_near_expiry(self, db_session, distribution_center, warehouse_location):
        """Verifica la detección de lotes cerca del vencimiento"""
        # Lote que vence en 20 días (cerca del vencimiento)
        batch_near = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=20)
        )
        
        # Lote que vence en 90 días (no cerca del vencimiento)
        batch_ok = ProductBatch(
            product_sku='TEST-002',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=100,
            expiry_date=date.today() + timedelta(days=90)
        )
        
        assert batch_near.is_near_expiry() is True
        assert batch_ok.is_near_expiry() is False
    
    def test_is_expired_check(self, db_session, distribution_center, warehouse_location):
        """Verifica la detección de lotes vencidos"""
        # Lote vencido
        batch_expired = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() - timedelta(days=10)
        )
        
        # Lote válido
        batch_valid = ProductBatch(
            product_sku='TEST-002',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=100,
            expiry_date=date.today() + timedelta(days=90)
        )
        
        assert batch_expired.is_expired_check is True
        assert batch_valid.is_expired_check is False
    
    def test_expiry_status(self, db_session, distribution_center, warehouse_location):
        """Verifica el estado de vencimiento"""
        # Lote vencido
        batch_expired = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() - timedelta(days=10)
        )
        
        # Lote cerca del vencimiento
        batch_near = ProductBatch(
            product_sku='TEST-002',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=100,
            expiry_date=date.today() + timedelta(days=20)
        )
        
        # Lote válido
        batch_valid = ProductBatch(
            product_sku='TEST-003',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-003',
            quantity=100,
            expiry_date=date.today() + timedelta(days=90)
        )
        
        assert batch_expired.expiry_status == 'expired'
        assert batch_near.expiry_status == 'near_expiry'
        assert batch_valid.expiry_status == 'valid'
    
    def test_temperature_range_property(self, db_session, distribution_center, warehouse_location):
        """Verifica la propiedad temperature_range"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            required_temperature_min=2.0,
            required_temperature_max=8.0
        )
        
        assert batch.temperature_range == '2.0°C - 8.0°C'
    
    def test_product_batch_to_dict(self, db_session, distribution_center, warehouse_location):
        """Verifica la serialización a diccionario"""
        expiry_date = date.today() + timedelta(days=180)
        manufactured_date = date.today() - timedelta(days=90)
        
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=expiry_date,
            manufactured_date=manufactured_date,
            required_temperature_min=2.0,
            required_temperature_max=8.0,
            barcode='7501234567890',
            qr_code='QR-TEST-001',
            internal_code='INT-001',
            is_available=True,
            is_expired=False,
            is_quarantine=False,
            notes='Lote de prueba'
        )
        db_session.add(batch)
        db_session.commit()
        
        batch_dict = batch.to_dict(include_location=False)
        
        assert batch_dict['id'] == batch.id
        assert batch_dict['product_sku'] == 'TEST-001'
        assert batch_dict['distribution_center_id'] == distribution_center.id
        assert batch_dict['location_id'] == warehouse_location.id
        assert batch_dict['batch_info']['batch_number'] == 'BATCH-001'
        assert batch_dict['batch_info']['quantity'] == 100
        assert batch_dict['batch_info']['barcode'] == '7501234567890'
        assert batch_dict['batch_info']['qr_code'] == 'QR-TEST-001'
        assert batch_dict['batch_info']['internal_code'] == 'INT-001'
        assert batch_dict['dates']['expiry_date'] == expiry_date.isoformat()
        assert batch_dict['dates']['manufactured_date'] == manufactured_date.isoformat()
        assert batch_dict['temperature_requirements']['min'] == 2.0
        assert batch_dict['temperature_requirements']['max'] == 8.0
        assert batch_dict['temperature_requirements']['range'] == '2.0°C - 8.0°C'
        assert batch_dict['status']['is_available'] is True
        assert batch_dict['status']['is_expired'] is False
        assert batch_dict['status']['is_quarantine'] is False
        assert batch_dict['notes'] == 'Lote de prueba'
    
    def test_product_batch_relationships(self, db_session, distribution_center, warehouse_location):
        """Verifica las relaciones del lote con otras entidades"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=distribution_center.id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180)
        )
        db_session.add(batch)
        db_session.commit()
        
        # Verificar relación con distribution_center
        assert batch.distribution_center is not None
        assert batch.distribution_center.id == distribution_center.id
        
        # Verificar relación con location
        assert batch.location is not None
        assert batch.location.id == warehouse_location.id
