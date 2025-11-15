"""
Tests para comandos de reservas de carrito.
"""

import pytest
from datetime import datetime, timedelta
from src.commands.cart_reservations import (
    ReserveStockCommand,
    ReleaseStockCommand,
    ExpireCartReservationsCommand,
    ClearUserCartReservationsCommand
)
from src.models.cart_reservation import CartReservation
from src.models.inventory import Inventory
from src.errors.errors import ValidationError, NotFoundError, ConflictError


class TestReserveStockCommand:
    """Tests para ReserveStockCommand."""
    
    def test_reserve_stock_success(self, db, sample_inventory, sample_distribution_center):
        """Test: Reservar stock exitosamente."""
        command = ReserveStockCommand(
            product_sku='JER-001',
            quantity=5,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        
        result = command.execute()
        
        assert result['success'] is True
        assert result['product_sku'] == 'JER-001'
        assert result['quantity_reserved'] == 5
        assert 'reservation_id' in result
        assert 'expires_at' in result
        
        # Verificar que se creó la reserva en BD
        reservation = CartReservation.query.filter_by(
            user_id='user123',
            session_id='session456',
            product_sku='JER-001'
        ).first()
        
        assert reservation is not None
        assert reservation.quantity_reserved == 5
        assert reservation.is_active is True
    
    def test_reserve_stock_insufficient(self, db, sample_inventory, sample_distribution_center):
        """Test: Error al intentar reservar más stock del disponible."""
        # sample_inventory tiene 100 unidades disponibles
        command = ReserveStockCommand(
            product_sku='JER-001',
            quantity=150,  # Más de lo disponible
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        
        with pytest.raises(ConflictError) as exc_info:
            command.execute()
        
        assert 'insuficiente' in str(exc_info.value).lower()
    
    def test_reserve_stock_update_existing(self, db, sample_inventory, sample_distribution_center):
        """Test: Actualizar reserva existente."""
        # Primera reserva
        command1 = ReserveStockCommand(
            product_sku='JER-001',
            quantity=5,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        result1 = command1.execute()
        
        # Segunda reserva (debe actualizar la primera)
        command2 = ReserveStockCommand(
            product_sku='JER-001',
            quantity=3,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        result2 = command2.execute()
        
        # Debe ser la misma reserva, con cantidad sumada
        assert result1['reservation_id'] == result2['reservation_id']
        assert result2['quantity_reserved'] == 8  # 5 + 3
    
    def test_reserve_stock_validation_errors(self, db, sample_distribution_center):
        """Test: Validación de parámetros."""
        # Sin product_sku
        with pytest.raises(ValidationError):
            command = ReserveStockCommand(
                product_sku='',
                quantity=5,
                user_id='user123',
                session_id='session456',
                distribution_center_id=sample_distribution_center.id
            )
            command.execute()
        
        # Cantidad negativa
        with pytest.raises(ValidationError):
            command = ReserveStockCommand(
                product_sku='JER-001',
                quantity=-5,
                user_id='user123',
                session_id='session456',
                distribution_center_id=sample_distribution_center.id
            )
            command.execute()
        
        # Sin user_id
        with pytest.raises(ValidationError):
            command = ReserveStockCommand(
                product_sku='JER-001',
                quantity=5,
                user_id='',
                session_id='session456',
                distribution_center_id=sample_distribution_center.id
            )
            command.execute()
    
    def test_reserve_stock_product_not_found(self, db, sample_distribution_center):
        """Test: Producto no existe en inventario."""
        command = ReserveStockCommand(
            product_sku='NOEXISTE',
            quantity=5,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        
        with pytest.raises(NotFoundError):
            command.execute()


class TestReleaseStockCommand:
    """Tests para ReleaseStockCommand."""
    
    def test_release_stock_success(self, db, sample_inventory, sample_distribution_center):
        """Test: Liberar stock exitosamente."""
        # Primero reservar
        reserve_cmd = ReserveStockCommand(
            product_sku='JER-001',
            quantity=10,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        reserve_cmd.execute()
        
        # Luego liberar parcialmente
        release_cmd = ReleaseStockCommand(
            product_sku='JER-001',
            quantity=4,
            user_id='user123',
            session_id='session456'
        )
        result = release_cmd.execute()
        
        assert result['success'] is True
        assert result['quantity_released'] == 4
        
        # Verificar que la reserva se actualizó
        reservation = CartReservation.query.filter_by(
            user_id='user123',
            session_id='session456',
            product_sku='JER-001'
        ).first()
        
        assert reservation.quantity_reserved == 6  # 10 - 4
        assert reservation.is_active is True
    
    def test_release_stock_complete(self, db, sample_inventory, sample_distribution_center):
        """Test: Liberar toda la reserva."""
        # Reservar
        reserve_cmd = ReserveStockCommand(
            product_sku='JER-001',
            quantity=10,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        reserve_cmd.execute()
        
        # Liberar todo
        release_cmd = ReleaseStockCommand(
            product_sku='JER-001',
            quantity=10,
            user_id='user123',
            session_id='session456'
        )
        result = release_cmd.execute()
        
        assert result['success'] is True
        
        # La reserva debe haber sido eliminada completamente
        reservation = CartReservation.query.filter_by(
            user_id='user123',
            session_id='session456',
            product_sku='JER-001'
        ).first()
        
        assert reservation is None  # Se eliminó la reserva al liberar todo
    
    def test_release_stock_no_reservation(self, db, sample_inventory):
        """Test: Intentar liberar sin tener reserva."""
        release_cmd = ReleaseStockCommand(
            product_sku='JER-001',
            quantity=5,
            user_id='user999',
            session_id='session999'
        )
        
        # No debe fallar, solo devolver success
        result = release_cmd.execute()
        assert result['success'] is True


class TestExpireCartReservationsCommand:
    """Tests para ExpireCartReservationsCommand."""
    
    def test_expire_old_reservations(self, db, sample_inventory, sample_distribution_center):
        """Test: Expirar reservas antiguas."""
        # Crear reserva expirada
        expired_reservation = CartReservation(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            user_id='user123',
            session_id='session456',
            quantity_reserved=5,
            created_at=datetime.utcnow() - timedelta(minutes=20),
            expires_at=datetime.utcnow() - timedelta(minutes=5),
            is_active=True
        )
        db.session.add(expired_reservation)
        
        # Crear reserva activa
        active_reservation = CartReservation(
            product_sku='VAC-001',
            distribution_center_id=sample_distribution_center.id,
            user_id='user789',
            session_id='session789',
            quantity_reserved=3,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        db.session.add(active_reservation)
        db.session.commit()
        
        # Ejecutar comando de expiración
        command = ExpireCartReservationsCommand()
        result = command.execute()
        
        assert result['success'] is True
        assert result['expired_count'] == 1
        assert 'JER-001' in result['products_affected']
        
        # Verificar que la reserva expirada está inactiva
        db.session.refresh(expired_reservation)
        assert expired_reservation.is_active is False
        
        # Verificar que la reserva activa sigue activa
        db.session.refresh(active_reservation)
        assert active_reservation.is_active is True
    
    def test_expire_no_reservations(self, db):
        """Test: No hay reservas para expirar."""
        command = ExpireCartReservationsCommand()
        result = command.execute()
        
        assert result['success'] is True
        assert result['expired_count'] == 0


class TestClearUserCartReservationsCommand:
    """Tests para ClearUserCartReservationsCommand."""
    
    def test_clear_user_cart(self, db, sample_inventory, sample_distribution_center):
        """Test: Limpiar carrito completo de un usuario."""
        # Crear múltiples reservas para el usuario
        reserve1 = ReserveStockCommand(
            product_sku='JER-001',
            quantity=5,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        reserve1.execute()
        
        # Agregar otro producto al inventario
        inventory2 = Inventory(
            product_sku='VAC-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=50,
            quantity_reserved=0
        )
        db.session.add(inventory2)
        db.session.commit()
        
        reserve2 = ReserveStockCommand(
            product_sku='VAC-001',
            quantity=3,
            user_id='user123',
            session_id='session456',
            distribution_center_id=sample_distribution_center.id
        )
        reserve2.execute()
        
        # Limpiar carrito
        clear_cmd = ClearUserCartReservationsCommand(
            user_id='user123',
            session_id='session456'
        )
        result = clear_cmd.execute()
        
        assert result['success'] is True
        assert result['cleared_count'] == 2
        assert len(result['products_affected']) == 2
        
        # Verificar que todas las reservas están inactivas
        reservations = CartReservation.query.filter_by(
            user_id='user123',
            session_id='session456'
        ).all()
        
        for reservation in reservations:
            assert reservation.is_active is False
    
    def test_clear_empty_cart(self, db):
        """Test: Limpiar carrito sin reservas."""
        clear_cmd = ClearUserCartReservationsCommand(
            user_id='user999',
            session_id='session999'
        )
        result = clear_cmd.execute()
        
        assert result['success'] is True
        assert result['cleared_count'] == 0
