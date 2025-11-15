"""
Tests para el comando GetRealTimeStock.
"""

import pytest
from datetime import datetime, timedelta
from src.commands.get_realtime_stock import GetRealTimeStock
from src.models.cart_reservation import CartReservation
from src.models.inventory import Inventory


class TestGetRealTimeStock:
    """Tests para GetRealTimeStock."""
    
    def test_get_stock_single_product(self, db, sample_inventory, sample_distribution_center):
        """Test: Obtener stock en tiempo real de un producto."""
        command = GetRealTimeStock(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        # Verificar estructura de respuesta
        assert result['product_sku'] == 'JER-001'
        assert result['total_physical_stock'] == 100
        assert result['total_reserved_in_carts'] == 0
        assert result['total_available_for_purchase'] == 100
        assert 'distribution_centers' in result
        assert len(result['distribution_centers']) > 0
    
    def test_get_stock_with_reservations(self, db, sample_inventory, sample_distribution_center):
        """Test: Stock con reservas activas."""
        # Crear reservas con expires_at
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        for i in range(3):
            reservation = CartReservation(
                product_sku='JER-001',
                distribution_center_id=sample_distribution_center.id,
                user_id=f'user{i}',
                session_id=f'session{i}',
                quantity_reserved=5,
                expires_at=expires_at,
                is_active=True
            )
            db.session.add(reservation)
        db.session.commit()
        
        command = GetRealTimeStock(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        assert result['total_reserved_in_carts'] == 15  # 3 * 5
        assert result['total_available_for_purchase'] == 85  # 100 - 15


class TestGetRealTimeStockEdgeCases:
    """Tests para casos edge de GetRealTimeStock."""
    
    def test_get_stock_product_not_found(self, db, sample_distribution_center):
        """Test: Producto que no existe retorna stock 0."""
        command = GetRealTimeStock(
            product_sku='NOEXISTE',
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        # Debe retornar estructura válida con stock 0
        assert result['product_sku'] == 'NOEXISTE'
        assert result['total_physical_stock'] == 0
        assert result['total_reserved_in_carts'] == 0
        assert result['total_available_for_purchase'] == 0
        assert result['distribution_centers'] == []
    
    def test_get_stock_multiple_products(self, db, sample_inventory, sample_distribution_center):
        """Test: Consultar stock de múltiples productos."""
        # Crear otro producto
        from src.models.inventory import Inventory
        inventory2 = Inventory(
            product_sku='VAC-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=75,
            quantity_reserved=0
        )
        db.session.add(inventory2)
        db.session.commit()
        
        command = GetRealTimeStock(
            product_skus=['JER-001', 'VAC-001'],
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        # Debe retornar formato de múltiples productos
        assert 'products' in result
        assert 'total_products' in result
        assert result['total_products'] == 2
        assert len(result['products']) == 2
    
    def test_get_stock_without_distribution_center(self, db, sample_inventory):
        """Test: Consultar stock sin especificar centro de distribución."""
        command = GetRealTimeStock(
            product_sku='JER-001'
        )
        
        result = command.execute()
        
        # Debe retornar stock de todos los centros
        assert result['product_sku'] == 'JER-001'
        assert result['total_physical_stock'] >= 0
    
    def test_get_stock_uppercase_normalization(self, db, sample_inventory, sample_distribution_center):
        """Test: SKU en minúsculas se normaliza a mayúsculas."""
        command = GetRealTimeStock(
            product_sku='jer-001',  # Minúsculas
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        # Debe encontrar el producto (normalizado a mayúsculas)
        assert result['product_sku'] == 'JER-001'
        assert result['total_physical_stock'] == 100
    
    def test_get_stock_out_of_stock_flag(self, db, sample_inventory, sample_distribution_center):
        """Test: Flag is_out_of_stock se marca correctamente."""
        # Reservar todo el stock
        expires_at = datetime.utcnow() + timedelta(minutes=15)
        reservation = CartReservation(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            user_id='user_oos',
            session_id='session_oos',
            quantity_reserved=100,  # Todo el stock
            expires_at=expires_at,
            is_active=True
        )
        db.session.add(reservation)
        db.session.commit()
        
        command = GetRealTimeStock(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        assert result['total_available_for_purchase'] == 0
        assert result['distribution_centers'][0]['is_out_of_stock'] is True
    
    def test_get_stock_distribution_center_details(self, db, sample_inventory, sample_distribution_center):
        """Test: Response incluye detalles del centro de distribución."""
        command = GetRealTimeStock(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        dc = result['distribution_centers'][0]
        assert 'distribution_center_id' in dc
        assert 'distribution_center_code' in dc
        assert 'distribution_center_name' in dc
        assert 'city' in dc
        assert dc['distribution_center_code'] == 'DC-001'

