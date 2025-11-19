"""
Tests para comandos de reserva de inventario para órdenes.

Prueba la funcionalidad de actualizar inventory.quantity_reserved
cuando se crea o cancela una orden.
"""

import pytest
from datetime import datetime
from src.commands.reserve_inventory_for_order import (
    ReserveInventoryForOrder,
    ReleaseInventoryForOrder
)
from src.models.inventory import Inventory
from src.errors.errors import ValidationError, NotFoundError, ConflictError


class TestReserveInventoryForOrder:
    """Tests para ReserveInventoryForOrder."""
    
    def test_reserve_success_single_item(self, db, sample_inventory, sample_distribution_center):
        """Test: Reservar inventario exitosamente para un item."""
        # Estado inicial
        initial_quantity_reserved = sample_inventory.quantity_reserved
        initial_quantity_available = sample_inventory.quantity_available
        
        command = ReserveInventoryForOrder(
            order_id='ORD-2025-001',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        result = command.execute()
        
        # Verificar resultado
        assert result['success'] is True
        assert result['order_id'] == 'ORD-2025-001'
        assert len(result['items_reserved']) == 1
        
        # Verificar item reservado
        reserved_item = result['items_reserved'][0]
        assert reserved_item['product_sku'] == 'JER-001'
        assert reserved_item['quantity_reserved'] == 10
        assert reserved_item['quantity_reserved_before'] == initial_quantity_reserved
        assert reserved_item['quantity_reserved_after'] == initial_quantity_reserved + 10
        
        # Verificar en base de datos
        db.session.refresh(sample_inventory)
        assert sample_inventory.quantity_reserved == initial_quantity_reserved + 10
        assert sample_inventory.quantity_available == initial_quantity_available  # NO cambia
    
    def test_reserve_success_multiple_items(self, db, sample_distribution_center):
        """Test: Reservar inventario para múltiples items."""
        # Crear múltiples inventarios
        inventory1 = Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0
        )
        inventory2 = Inventory(
            product_sku='MED-002',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=200,
            quantity_reserved=0,
            quantity_in_transit=0
        )
        db.session.add_all([inventory1, inventory2])
        db.session.commit()
        
        command = ReserveInventoryForOrder(
            order_id='ORD-2025-002',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'distribution_center_id': sample_distribution_center.id
                },
                {
                    'product_sku': 'MED-002',
                    'quantity': 25,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        result = command.execute()
        
        assert result['success'] is True
        assert len(result['items_reserved']) == 2
        
        # Verificar ambos items en BD
        db.session.refresh(inventory1)
        db.session.refresh(inventory2)
        assert inventory1.quantity_reserved == 10
        assert inventory2.quantity_reserved == 25
        assert inventory1.quantity_available == 100  # Sin cambios
        assert inventory2.quantity_available == 200  # Sin cambios
    
    def test_reserve_insufficient_stock(self, db, sample_inventory, sample_distribution_center):
        """Test: Error al intentar reservar más stock del disponible."""
        # sample_inventory tiene quantity_available = 500
        command = ReserveInventoryForOrder(
            order_id='ORD-2025-003',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 600,  # Más del disponible
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        with pytest.raises(ConflictError) as exc_info:
            command.execute()
        
        assert 'Stock insuficiente' in str(exc_info.value)
        assert 'JER-001' in str(exc_info.value)
    
    def test_reserve_product_not_found(self, db, sample_distribution_center):
        """Test: Error cuando el producto no existe en inventario."""
        command = ReserveInventoryForOrder(
            order_id='ORD-2025-004',
            items=[
                {
                    'product_sku': 'NONEXISTENT',
                    'quantity': 10,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            command.execute()
        
        assert 'No se encontró inventario' in str(exc_info.value)
        assert 'NONEXISTENT' in str(exc_info.value)
    
    def test_reserve_validation_errors(self, db):
        """Test: Validación de parámetros."""
        # Sin order_id
        with pytest.raises(ValidationError) as exc_info:
            command = ReserveInventoryForOrder(order_id='', items=[])
            command.execute()
        assert 'order_id es requerido' in str(exc_info.value)
        
        # Sin items
        with pytest.raises(ValidationError) as exc_info:
            command = ReserveInventoryForOrder(order_id='ORD-001', items=[])
            command.execute()
        assert 'lista no vacía' in str(exc_info.value) or 'al menos un item' in str(exc_info.value)
        
        # Item sin product_sku
        with pytest.raises(ValidationError) as exc_info:
            command = ReserveInventoryForOrder(
                order_id='ORD-001',
                items=[{'quantity': 10}]
            )
            command.execute()
        assert 'product_sku es requerido' in str(exc_info.value)
        
        # Item sin quantity
        with pytest.raises(ValidationError) as exc_info:
            command = ReserveInventoryForOrder(
                order_id='ORD-001',
                items=[{'product_sku': 'JER-001'}]
            )
            command.execute()
        assert 'quantity es requerido' in str(exc_info.value)
        
        # Quantity negativa
        with pytest.raises(ValidationError) as exc_info:
            command = ReserveInventoryForOrder(
                order_id='ORD-001',
                items=[{
                    'product_sku': 'JER-001',
                    'quantity': -5,
                    'distribution_center_id': 1
                }]
            )
            command.execute()
        assert 'número positivo' in str(exc_info.value)
    
    def test_reserve_atomic_transaction(self, db, sample_distribution_center):
        """Test: Rollback si falla algún item (transacción atómica)."""
        # Crear inventarios
        inventory1 = Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=100,
            quantity_reserved=0,
            quantity_in_transit=0
        )
        inventory2 = Inventory(
            product_sku='MED-002',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=50,
            quantity_reserved=0,
            quantity_in_transit=0
        )
        db.session.add_all([inventory1, inventory2])
        db.session.commit()
        
        # Intentar reservar: primer item OK, segundo item falla (stock insuficiente)
        command = ReserveInventoryForOrder(
            order_id='ORD-2025-005',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'distribution_center_id': sample_distribution_center.id
                },
                {
                    'product_sku': 'MED-002',
                    'quantity': 100,  # Más del disponible
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        with pytest.raises(ConflictError):
            command.execute()
        
        # Verificar rollback: inventory1 NO debe tener reserva
        db.session.refresh(inventory1)
        db.session.refresh(inventory2)
        assert inventory1.quantity_reserved == 0  # Rollback exitoso
        assert inventory2.quantity_reserved == 0


class TestReleaseInventoryForOrder:
    """Tests para ReleaseInventoryForOrder."""
    
    def test_release_success(self, db, sample_distribution_center):
        """Test: Liberar inventario exitosamente."""
        # Crear inventario con reservas
        inventory = Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=500,
            quantity_reserved=50,  # Ya tiene reservas
            quantity_in_transit=0
        )
        db.session.add(inventory)
        db.session.commit()
        
        command = ReleaseInventoryForOrder(
            order_id='ORD-2025-001',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 20,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        result = command.execute()
        
        assert result['success'] is True
        assert result['order_id'] == 'ORD-2025-001'
        assert len(result['items_released']) == 1
        
        # Verificar item liberado
        released_item = result['items_released'][0]
        assert released_item['product_sku'] == 'JER-001'
        assert released_item['quantity_released'] == 20
        assert released_item['quantity_reserved_before'] == 50
        assert released_item['quantity_reserved_after'] == 30
        
        # Verificar en BD
        db.session.refresh(inventory)
        assert inventory.quantity_reserved == 30
        assert inventory.quantity_available == 500  # NO cambia
    
    def test_release_multiple_items(self, db, sample_distribution_center):
        """Test: Liberar inventario para múltiples items."""
        inventory1 = Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=500,
            quantity_reserved=50,
            quantity_in_transit=0
        )
        inventory2 = Inventory(
            product_sku='MED-002',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=300,
            quantity_reserved=30,
            quantity_in_transit=0
        )
        db.session.add_all([inventory1, inventory2])
        db.session.commit()
        
        command = ReleaseInventoryForOrder(
            order_id='ORD-2025-002',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 20,
                    'distribution_center_id': sample_distribution_center.id
                },
                {
                    'product_sku': 'MED-002',
                    'quantity': 15,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        result = command.execute()
        
        assert result['success'] is True
        assert len(result['items_released']) == 2
        
        db.session.refresh(inventory1)
        db.session.refresh(inventory2)
        assert inventory1.quantity_reserved == 30  # 50 - 20
        assert inventory2.quantity_reserved == 15  # 30 - 15
    
    def test_release_more_than_reserved(self, db, sample_distribution_center):
        """Test: Intentar liberar más de lo reservado (solo libera lo disponible)."""
        inventory = Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=500,
            quantity_reserved=10,  # Solo 10 reservadas
            quantity_in_transit=0
        )
        db.session.add(inventory)
        db.session.commit()
        
        # Intentar liberar 20 cuando solo hay 10 reservadas
        command = ReleaseInventoryForOrder(
            order_id='ORD-2025-003',
            items=[
                {
                    'product_sku': 'JER-001',
                    'quantity': 20,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        result = command.execute()
        
        # Debe liberar solo 10 (lo que estaba reservado)
        assert result['success'] is True
        released_item = result['items_released'][0]
        assert released_item['quantity_released'] == 10  # No 20
        
        db.session.refresh(inventory)
        assert inventory.quantity_reserved == 0
    
    def test_release_product_not_found(self, db, sample_distribution_center):
        """Test: Error cuando el producto no existe."""
        command = ReleaseInventoryForOrder(
            order_id='ORD-2025-004',
            items=[
                {
                    'product_sku': 'NONEXISTENT',
                    'quantity': 10,
                    'distribution_center_id': sample_distribution_center.id
                }
            ]
        )
        
        with pytest.raises(NotFoundError) as exc_info:
            command.execute()
        
        assert 'No se encontró inventario' in str(exc_info.value)
