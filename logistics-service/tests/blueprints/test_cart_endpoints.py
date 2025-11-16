"""
Tests para los endpoints REST de carrito (/cart/*).
"""

import pytest
import json
from datetime import datetime, timedelta
from src.models.cart_reservation import CartReservation
from src.models.inventory import Inventory


class TestCartReserveEndpoint:
    """Tests para POST /cart/reserve"""
    
    def test_reserve_cart_success(self, client, sample_inventory, sample_distribution_center):
        """Test: Reservar stock exitosamente vía API."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 5,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['product_sku'] == 'JER-001'
        assert data['quantity_reserved'] == 5
        assert 'reservation_id' in data
        assert 'expires_at' in data
    
    def test_reserve_cart_insufficient_stock(self, client, sample_inventory, sample_distribution_center):
        """Test: Error al reservar más stock del disponible."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 200,  # Más de lo disponible
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
        assert 'insufficient' in data['error'].lower() or 'stock' in data['error'].lower()
    
    def test_reserve_cart_missing_fields(self, client):
        """Test: Error al enviar request sin campos requeridos."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'JER-001'
            # Faltan quantity, user_id, etc.
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_reserve_cart_invalid_quantity(self, client, sample_distribution_center):
        """Test: Error al enviar cantidad negativa."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': -5,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_reserve_cart_product_not_found(self, client, sample_distribution_center):
        """Test: Error cuando producto no existe."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'NOEXISTE',
            'quantity': 5,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_reserve_cart_no_json_body(self, client):
        """Test: Error al enviar request sin body JSON."""
        response = client.post('/cart/reserve')
        
        # El endpoint puede retornar 400 o 500 dependiendo de cómo Flask maneja el error
        assert response.status_code in [400, 500]


class TestCartReleaseEndpoint:
    """Tests para POST /cart/release"""
    
    def test_release_cart_success(self, client, db, sample_inventory, sample_distribution_center):
        """Test: Liberar stock exitosamente vía API."""
        # Primero reservar
        client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 10,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        # Luego liberar parcialmente
        response = client.post('/cart/release', json={
            'product_sku': 'JER-001',
            'quantity': 4,
            'user_id': 'user123',
            'session_id': 'session456'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['quantity_released'] == 4
    
    def test_release_cart_no_reservation(self, client):
        """Test: Intentar liberar sin tener reserva."""
        response = client.post('/cart/release', json={
            'product_sku': 'JER-001',
            'quantity': 5,
            'user_id': 'user999',
            'session_id': 'session999'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_release_cart_full_release(self, client, db, sample_inventory, sample_distribution_center):
        """Test: Liberar toda la reserva."""
        # Reservar
        client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 10,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        # Liberar todo
        response = client.post('/cart/release', json={
            'product_sku': 'JER-001',
            'quantity': 10,
            'user_id': 'user123',
            'session_id': 'session456'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verificar que la reserva fue eliminada
        reservation = CartReservation.query.filter_by(
            user_id='user123',
            session_id='session456',
            product_sku='JER-001'
        ).first()
        assert reservation is None
    
    def test_release_cart_missing_fields(self, client):
        """Test: Error al enviar request sin campos."""
        response = client.post('/cart/release', json={
            'product_sku': 'JER-001'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestCartClearEndpoint:
    """Tests para DELETE /cart/clear"""
    
    def test_clear_cart_success(self, client, db, sample_inventory, sample_distribution_center):
        """Test: Limpiar carrito completo."""
        # Crear múltiples reservas
        client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 5,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        # Limpiar carrito
        response = client.delete('/cart/clear', json={
            'user_id': 'user123',
            'session_id': 'session456'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['cleared_count'] >= 0
    
    def test_clear_cart_empty(self, client):
        """Test: Limpiar carrito vacío."""
        response = client.delete('/cart/clear', json={
            'user_id': 'user999',
            'session_id': 'session999'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['cleared_count'] == 0
    
    def test_clear_cart_missing_user_id(self, client):
        """Test: Error al no enviar user_id."""
        response = client.delete('/cart/clear', json={
            'session_id': 'session456'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestCartReservationsEndpoint:
    """Tests para GET /cart/reservations"""
    
    def test_get_reservations_success(self, client, db, sample_inventory, sample_distribution_center):
        """Test: Obtener reservas activas."""
        # Crear reserva
        client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 5,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        response = client.get('/cart/reservations?user_id=user123&session_id=session456')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'reservations' in data
        assert len(data['reservations']) > 0
    
    def test_get_reservations_empty(self, client):
        """Test: Obtener reservas cuando no hay ninguna."""
        response = client.get('/cart/reservations?user_id=user999&session_id=session999')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert len(data['reservations']) == 0
    
    def test_get_reservations_missing_params(self, client):
        """Test: Error al no enviar parámetros requeridos."""
        response = client.get('/cart/reservations')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestCartEdgeCases:
    """Tests para casos edge de cart endpoints."""
    
    def test_reserve_cart_with_empty_json(self, client):
        """Test: Error al enviar JSON vacío."""
        response = client.post('/cart/reserve', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_release_cart_with_empty_json(self, client):
        """Test: Error al liberar con JSON vacío."""
        response = client.post('/cart/release', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_clear_cart_with_empty_json(self, client):
        """Test: Error al limpiar con JSON vacío."""
        response = client.delete('/cart/clear', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_reserve_cart_missing_json_content_type(self, client):
        """Test: Request sin Content-Type application/json."""
        response = client.post('/cart/reserve', data='invalid')
        
        # Flask retorna 400 o 500 dependiendo del handler
        assert response.status_code in [400, 415, 500]
    
    def test_release_cart_partial_release(self, client, db, sample_inventory, sample_distribution_center):
        """Test: Liberar parcialmente una reserva."""
        # Primero reservar
        client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 20,
            'user_id': 'user_partial',
            'session_id': 'session_partial',
            'distribution_center_id': sample_distribution_center.id
        })
        
        # Liberar solo 10
        response = client.post('/cart/release', json={
            'product_sku': 'JER-001',
            'quantity': 10,
            'user_id': 'user_partial',
            'session_id': 'session_partial'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_reserve_with_zero_quantity(self, client, sample_distribution_center):
        """Test: Reservar con cantidad 0."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 0,
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_reserve_with_string_quantity(self, client, sample_distribution_center):
        """Test: Reservar con cantidad como string."""
        response = client.post('/cart/reserve', json={
            'product_sku': 'JER-001',
            'quantity': 'cinco',
            'user_id': 'user123',
            'session_id': 'session456',
            'distribution_center_id': sample_distribution_center.id
        })
        
        assert response.status_code in [400, 500]

