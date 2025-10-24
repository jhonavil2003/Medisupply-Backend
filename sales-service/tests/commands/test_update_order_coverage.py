"""
Tests adicionales para aumentar cobertura de UpdateOrder.
Estos tests cubren casos edge y manejo de errores.
"""
import pytest
from decimal import Decimal
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from unittest.mock import patch, MagicMock
from src.commands.update_order import UpdateOrder
from src.models.order import Order
from src.errors.errors import DatabaseError, ValidationError, ApiError


class TestUpdateOrderCoverage:
    """Tests para aumentar cobertura de UpdateOrder."""
    
    def test_update_order_database_integrity_error(self, db, sample_order, monkeypatch):
        """Test que un IntegrityError se convierte en DatabaseError."""
        update_data = {
            'notes': 'Updated notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        # Simular IntegrityError en commit
        original_commit = db.session.commit
        def mock_commit():
            raise IntegrityError("mock statement", "mock params", "mock orig")
        
        monkeypatch.setattr(db.session, 'commit', mock_commit)
        
        with pytest.raises(DatabaseError) as exc_info:
            command.execute()
        
        assert "Database integrity error" in str(exc_info.value)
    
    def test_update_order_database_sqlalchemy_error(self, db, sample_order, monkeypatch):
        """Test que un SQLAlchemyError se convierte en DatabaseError."""
        update_data = {
            'notes': 'Updated notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        # Simular SQLAlchemyError en commit
        def mock_commit():
            raise SQLAlchemyError("Database error")
        
        monkeypatch.setattr(db.session, 'commit', mock_commit)
        
        with pytest.raises(DatabaseError) as exc_info:
            command.execute()
        
        assert "Database error while updating order" in str(exc_info.value)
    
    def test_update_order_unexpected_exception(self, db, sample_order, monkeypatch):
        """Test que una excepción inesperada se convierte en DatabaseError."""
        update_data = {
            'notes': 'Updated notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        # Simular una excepción inesperada
        def mock_commit():
            raise RuntimeError("Unexpected error")
        
        monkeypatch.setattr(db.session, 'commit', mock_commit)
        
        with pytest.raises(DatabaseError) as exc_info:
            command.execute()
        
        assert "Unexpected error while updating order" in str(exc_info.value)
    
    def test_update_order_item_validation_invalid_discount(self, db, sample_order):
        """Test validación de discount_percentage > 100."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'discount_percentage': 150.0  # Inválido: > 100
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "discount_percentage" in str(exc_info.value).lower()
        assert "100" in str(exc_info.value)
    
    def test_update_order_item_validation_negative_tax(self, db, sample_order):
        """Test validación de tax_percentage negativo."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'tax_percentage': -5.0  # Inválido: negativo
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        # El mensaje puede ser sobre 'negative' o sobre rango 0-100
        error_msg = str(exc_info.value).lower()
        assert "tax_percentage" in error_msg
        assert ("negative" in error_msg or "0" in error_msg)
    
    def test_update_order_invalid_status_transition_shipped_to_pending(self, db, sample_order):
        """Test transición inválida: shipped -> pending."""
        # Cambiar orden a shipped
        sample_order.status = 'shipped'
        db.session.commit()
        
        update_data = {
            'status': 'pending'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
        assert "solo se pueden editar órdenes pendientes" in str(exc_info.value).lower()
    
    def test_update_order_invalid_status_transition_delivered_to_confirmed(self, db, sample_order):
        """Test transición inválida: delivered -> confirmed."""
        # Cambiar orden a delivered
        sample_order.status = 'delivered'
        db.session.commit()
        
        update_data = {
            'status': 'confirmed'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert exc_info.value.status_code == 400
    
    def test_update_order_recalculate_totals_with_no_items(self, db, sample_order):
        """Test recálculo de totales cuando no hay items."""
        # Actualizar sin items debería mantener items existentes
        update_data = {
            'notes': 'Just updating notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Debe tener los items originales
        assert len(result['items']) >= 2
        assert result['total_amount'] > 0
    
    def test_update_order_item_with_zero_discount(self, db, sample_order):
        """Test item con discount_percentage = 0."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'discount_percentage': 0.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verificar cálculos
        item = result['items'][0]
        assert item['discount_amount'] == 0.0
        assert item['subtotal'] == 10000.0  # 10 * 1000
        assert item['tax_amount'] == 1900.0  # 10000 * 0.19
    
    def test_update_order_item_with_100_percent_discount(self, db, sample_order):
        """Test item con discount_percentage = 100."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 10,
                    'unit_price': 1000.0,
                    'discount_percentage': 100.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verificar cálculos
        item = result['items'][0]
        assert item['discount_amount'] == 10000.0  # 100% de descuento
        assert item['subtotal'] == 0.0  # Después del descuento
        assert item['tax_amount'] == 0.0  # Sin tax porque subtotal es 0
    
    def test_update_order_removes_all_immutable_fields(self, db, sample_order):
        """Test que todos los campos inmutables se remueven silenciosamente."""
        original_customer_id = sample_order.customer_id
        original_order_number = sample_order.order_number
        original_seller_id = sample_order.seller_id
        
        update_data = {
            'customer_id': 99999,
            'seller_id': 'NEW-SELLER',
            'seller_name': 'New Name',
            'order_number': 'ORD-FAKE',
            'order_date': '2025-01-01',
            'created_at': '2025-01-01',
            'subtotal': 999999.0,
            'discount_amount': 999999.0,
            'tax_amount': 999999.0,
            'total_amount': 999999.0,
            'notes': 'Valid update'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verificar que campos inmutables NO cambiaron
        assert result['customer_id'] == original_customer_id
        assert result['order_number'] == original_order_number
        assert result['seller_id'] == original_seller_id
        
        # Verificar que campo válido SÍ cambió
        assert result['notes'] == 'Valid update'
    
    def test_update_order_invalid_status_value(self, db, sample_order):
        """Test con un valor de status inválido."""
        update_data = {
            'status': 'invalid_status'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "invalid status" in str(exc_info.value).lower()
    
    def test_update_order_item_invalid_data_format(self, db, sample_order):
        """Test con formato de datos inválido en item."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 'invalid',  # Debería ser número
                    'unit_price': 1000.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "quantity" in str(exc_info.value).lower()
    
    def test_update_order_preserves_customer_relationship(self, db, sample_order):
        """Test que la relación con customer se preserva después de update."""
        original_customer_id = sample_order.customer_id
        
        update_data = {
            'notes': 'Updated notes'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verificar que customer está presente y correcto
        assert 'customer' in result
        assert result['customer'] is not None
        assert result['customer']['id'] == original_customer_id
