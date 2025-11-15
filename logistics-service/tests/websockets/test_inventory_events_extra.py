"""
Tests adicionales para inventory events.
"""

import pytest
from datetime import datetime
from src.websockets.inventory_events import (
    InventoryChangeType,
    InventoryEvent,
    InventoryEventDetector
)


class TestInventoryEventDetector:
    """Tests para InventoryEventDetector."""
    
    def test_detect_out_of_stock(self):
        """Test: Detecta cuando producto se agota."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=10,
            new_quantity=0
        )
        
        assert change_type == InventoryChangeType.OUT_OF_STOCK
    
    def test_detect_restock_from_zero(self):
        """Test: Detecta reabastecimiento desde 0."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=0,
            new_quantity=50
        )
        
        assert change_type == InventoryChangeType.RESTOCK
    
    def test_detect_low_stock_below_minimum(self):
        """Test: Detecta stock bajo cuando cae por debajo del mínimo."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=15,
            new_quantity=5,
            minimum_stock_level=10
        )
        
        assert change_type == InventoryChangeType.LOW_STOCK
    
    def test_detect_low_stock_at_reorder_point(self):
        """Test: Detecta stock bajo en punto de reorden."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=25,
            new_quantity=19,
            reorder_point=20
        )
        
        assert change_type == InventoryChangeType.LOW_STOCK
    
    def test_detect_sale(self):
        """Test: Detecta venta (disminución de stock)."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=100,
            new_quantity=95
        )
        
        assert change_type == InventoryChangeType.SALE
    
    def test_detect_restock_significant_increase(self):
        """Test: Detecta reabastecimiento con incremento significativo."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=50,
            new_quantity=75  # Incremento del 50%
        )
        
        assert change_type == InventoryChangeType.RESTOCK
    
    def test_detect_update_minor_change(self):
        """Test: Detecta actualización con cambio menor."""
        change_type = InventoryEventDetector.detect_change_type(
            previous_quantity=100,
            new_quantity=105  # Incremento del 5%
        )
        
        assert change_type == InventoryChangeType.UPDATE
    
    def test_should_notify_significant_change(self):
        """Test: Notifica cambio significativo."""
        should_notify = InventoryEventDetector.should_notify(
            previous_quantity=100,
            new_quantity=90,  # Cambio del 10%
            minimum_threshold_percentage=5.0
        )
        
        assert should_notify is True
    
    def test_should_not_notify_minor_change(self):
        """Test: No notifica cambio menor."""
        should_notify = InventoryEventDetector.should_notify(
            previous_quantity=100,
            new_quantity=98,  # Cambio del 2%
            minimum_threshold_percentage=5.0
        )
        
        assert should_notify is False
    
    def test_should_notify_from_zero(self):
        """Test: Notifica cualquier cambio desde 0."""
        should_notify = InventoryEventDetector.should_notify(
            previous_quantity=0,
            new_quantity=10,
            minimum_threshold_percentage=5.0
        )
        
        assert should_notify is True


class TestInventoryEventMethods:
    """Tests para métodos de InventoryEvent."""
    
    def test_is_significant_change_above_threshold(self):
        """Test: Cambio significativo por encima del umbral."""
        event = InventoryEvent(
            product_sku='TEST-001',
            distribution_center_id=1,
            previous_quantity=100,
            new_quantity=80,
            change_type=InventoryChangeType.SALE
        )
        
        # Cambio del 20% es significativo con umbral de 10%
        assert event.is_significant_change(threshold_percentage=10.0) is True
    
    def test_is_significant_change_below_threshold(self):
        """Test: Cambio no significativo por debajo del umbral."""
        event = InventoryEvent(
            product_sku='TEST-001',
            distribution_center_id=1,
            previous_quantity=100,
            new_quantity=95,
            change_type=InventoryChangeType.SALE
        )
        
        # Cambio del 5% no es significativo con umbral de 10%
        assert event.is_significant_change(threshold_percentage=10.0) is False
    
    def test_is_significant_change_from_zero(self):
        """Test: Cualquier cambio desde 0 es significativo."""
        event = InventoryEvent(
            product_sku='TEST-001',
            distribution_center_id=1,
            previous_quantity=0,
            new_quantity=5,
            change_type=InventoryChangeType.RESTOCK
        )
        
        assert event.is_significant_change(threshold_percentage=50.0) is True
    
    def test_event_to_dict(self):
        """Test: InventoryEvent.to_dict() incluye todos los campos."""
        event = InventoryEvent(
            product_sku='TEST-001',
            distribution_center_id=1,
            previous_quantity=50,
            new_quantity=45,
            change_type=InventoryChangeType.SALE
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['product_sku'] == 'TEST-001'
        assert event_dict['distribution_center_id'] == 1
        assert event_dict['previous_quantity'] == 50
        assert event_dict['new_quantity'] == 45
        assert event_dict['quantity_change'] == -5
        assert event_dict['change_type'] == InventoryChangeType.SALE
        assert 'timestamp' in event_dict
