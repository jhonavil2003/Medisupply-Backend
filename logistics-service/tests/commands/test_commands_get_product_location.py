import pytest
from datetime import date, timedelta
from src.commands.get_product_location import GetProductLocation
from src.models.product_batch import ProductBatch
from src.models.warehouse_location import WarehouseLocation
from src.errors.errors import ValidationError, NotFoundError


class TestGetProductLocation:
    """Tests para el comando GetProductLocation"""
    
    def test_search_by_product_sku(self, db, warehouse_location):
        """Verifica búsqueda por SKU de producto"""
        # Crear lotes de prueba
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
            expiry_date=date.today() + timedelta(days=90),
            is_available=True
        )
        db.session.add_all([batch1, batch2])
        db.session.commit()
        
        # Ejecutar comando
        command = GetProductLocation(product_sku='TEST-001')
        result = command.execute()
        
        assert result['found'] is True
        assert len(result['product_skus']) == 1
        assert 'TEST-001' in result['product_skus']
        assert result['total_locations'] == 2
        assert result['total_quantity'] == 150
    
    def test_search_by_barcode(self, db, warehouse_location):
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
        
        # Ejecutar comando
        command = GetProductLocation(barcode='7501234567890')
        result = command.execute()
        
        assert result['found'] is True
        assert result['total_locations'] == 1
        assert result['locations'][0]['batch']['batch_info']['barcode'] == '7501234567890'
    
    def test_search_by_qr_code(self, db, warehouse_location):
        """Verifica búsqueda por código QR"""
        batch = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            qr_code='QR-TEST-001',
            is_available=True
        )
        db.session.add(batch)
        db.session.commit()
        
        # Ejecutar comando
        command = GetProductLocation(qr_code='QR-TEST-001')
        result = command.execute()
        
        assert result['found'] is True
        assert result['total_locations'] == 1
        assert result['locations'][0]['batch']['batch_info']['qr_code'] == 'QR-TEST-001'
    
    def test_search_term_general(self, db, warehouse_location):
        """Verifica búsqueda general con search_term"""
        batch = ProductBatch(
            product_sku='GUANTE-001',
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
        
        # Búsqueda por término que coincide con SKU
        command = GetProductLocation(search_term='GUANTE')
        result = command.execute()
        
        assert result['found'] is True
        assert result['total_locations'] == 1
    
    def test_fefo_ordering(self, db, warehouse_location):
        """Verifica ordenamiento FEFO (First-Expire-First-Out)"""
        # Crear lotes con diferentes fechas de vencimiento
        batch1 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),  # Vence más tarde
            is_available=True
        )
        batch2 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=30),  # Vence primero
            is_available=True
        )
        batch3 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-003',
            quantity=75,
            expiry_date=date.today() + timedelta(days=90),  # Vence en medio
            is_available=True
        )
        db.session.add_all([batch1, batch2, batch3])
        db.session.commit()
        
        # Ejecutar comando con ordenamiento FEFO
        command = GetProductLocation(product_sku='TEST-001', order_by='fefo')
        result = command.execute()
        
        assert result['total_locations'] == 3
        # Verificar que el orden es FEFO (primero el que vence más pronto)
        assert result['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-002'
        assert result['locations'][1]['batch']['batch_info']['batch_number'] == 'BATCH-003'
        assert result['locations'][2]['batch']['batch_info']['batch_number'] == 'BATCH-001'
    
    def test_filter_by_zone_type(self, db, warehouse_location, warehouse_location_ambient):
        """Verifica filtrado por tipo de zona"""
        # Lote en zona refrigerada
        batch_cold = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        # Lote en zona ambiente
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
        
        # Filtrar solo zona refrigerada
        command = GetProductLocation(product_sku='TEST-001', zone_type='refrigerated')
        result = command.execute()
        
        assert result['total_locations'] == 1
        assert result['locations'][0]['physical_location']['zone_type'] == 'refrigerated'
        
        # Filtrar solo zona ambiente
        command = GetProductLocation(product_sku='TEST-001', zone_type='ambient')
        result = command.execute()
        
        assert result['total_locations'] == 1
        assert result['locations'][0]['physical_location']['zone_type'] == 'ambient'
    
    def test_filter_by_expiry_date_range(self, db, warehouse_location):
        """Verifica filtrado por rango de fechas de vencimiento"""
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
        
        # Filtrar por rango que solo incluye batch1
        expiry_from = date.today().isoformat()
        expiry_to = (date.today() + timedelta(days=60)).isoformat()
        
        command = GetProductLocation(
            product_sku='TEST-001',
            expiry_date_from=expiry_from,
            expiry_date_to=expiry_to
        )
        result = command.execute()
        
        assert result['total_locations'] == 1
        assert result['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-001'
    
    def test_exclude_expired_batches(self, db, warehouse_location):
        """Verifica que por defecto se excluyen lotes vencidos"""
        # Lote vencido
        batch_expired = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() - timedelta(days=10),
            is_available=True
        )
        # Lote válido
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
        
        # Sin incluir vencidos (default)
        command = GetProductLocation(product_sku='TEST-001', include_expired=False)
        result = command.execute()
        
        assert result['total_locations'] == 1
        assert result['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-002'
        
        # Incluyendo vencidos
        command = GetProductLocation(product_sku='TEST-001', include_expired=True)
        result = command.execute()
        
        assert result['total_locations'] == 2
    
    def test_only_available_filter(self, db, warehouse_location):
        """Verifica filtro de solo disponibles"""
        batch_available = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        batch_unavailable = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=50,
            expiry_date=date.today() + timedelta(days=180),
            is_available=False
        )
        db.session.add_all([batch_available, batch_unavailable])
        db.session.commit()
        
        # Solo disponibles (default)
        command = GetProductLocation(product_sku='TEST-001', only_available=True)
        result = command.execute()
        
        assert result['total_locations'] == 1
        assert result['locations'][0]['batch']['status']['is_available'] is True
    
    def test_no_search_parameter_validation_error(self):
        """Verifica error cuando no se proporciona parámetro de búsqueda"""
        command = GetProductLocation()
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "Se requiere al menos un parámetro de búsqueda" in str(exc_info.value)
    
    def test_invalid_zone_type_validation_error(self):
        """Verifica error con tipo de zona inválido"""
        command = GetProductLocation(product_sku='TEST-001', zone_type='invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "zone_type debe ser 'refrigerated' o 'ambient'" in str(exc_info.value)
    
    def test_invalid_order_by_validation_error(self):
        """Verifica error con criterio de ordenamiento inválido"""
        command = GetProductLocation(product_sku='TEST-001', order_by='invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "order_by debe ser" in str(exc_info.value)
    
    def test_invalid_date_format_validation_error(self):
        """Verifica error con formato de fecha inválido"""
        command = GetProductLocation(
            product_sku='TEST-001',
            expiry_date_from='2025-13-01'  # Mes inválido
        )
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "formato YYYY-MM-DD" in str(exc_info.value)
    
    def test_product_not_found_error(self, db):
        """Verifica error cuando no se encuentra el producto"""
        command = GetProductLocation(product_sku='NONEXISTENT-SKU')
        
        with pytest.raises(NotFoundError) as exc_info:
            command.execute()
        
        assert "Producto no encontrado" in str(exc_info.value)
    
    def test_temperature_info_for_refrigerated_zone(self, db, warehouse_location):
        """Verifica que se incluye información de temperatura para zonas refrigeradas"""
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
        
        command = GetProductLocation(product_sku='TEST-001')
        result = command.execute()
        
        assert 'temperature_status' in result['locations'][0]
        assert result['locations'][0]['temperature_status']['required_range'] == '2.0°C - 8.0°C'
        assert result['locations'][0]['temperature_status']['in_range'] is True
    
    def test_filter_by_batch_number(self, db, warehouse_location):
        """Verifica filtrado por número de lote"""
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
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        db.session.add_all([batch1, batch2])
        db.session.commit()
        
        command = GetProductLocation(product_sku='TEST-001', batch_number='BATCH-001')
        result = command.execute()
        
        assert result['total_locations'] == 1
        assert result['locations'][0]['batch']['batch_info']['batch_number'] == 'BATCH-001'
    
    def test_ordering_by_quantity(self, db, warehouse_location):
        """Verifica ordenamiento por cantidad"""
        batch1 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-001',
            quantity=50,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        batch2 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-002',
            quantity=150,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        batch3 = ProductBatch(
            product_sku='TEST-001',
            distribution_center_id=warehouse_location.distribution_center_id,
            location_id=warehouse_location.id,
            batch_number='BATCH-003',
            quantity=100,
            expiry_date=date.today() + timedelta(days=180),
            is_available=True
        )
        db.session.add_all([batch1, batch2, batch3])
        db.session.commit()
        
        command = GetProductLocation(product_sku='TEST-001', order_by='quantity')
        result = command.execute()
        
        # Verificar orden descendente por cantidad
        assert result['locations'][0]['batch']['batch_info']['quantity'] == 150
        assert result['locations'][1]['batch']['batch_info']['quantity'] == 100
        assert result['locations'][2]['batch']['batch_info']['quantity'] == 50
