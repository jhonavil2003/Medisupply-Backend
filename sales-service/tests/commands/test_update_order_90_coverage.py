"""
Tests adicionales para alcanzar 90% de cobertura en update_order.py

Este archivo contiene tests específicos para cubrir las líneas faltantes:
- Validaciones de formato de datos
- Validaciones de campos numéricos 
- Validaciones de tax_percentage
- Errores de TypeError/ValueError en items
- Validaciones de product_sku vacío
"""

import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from src.commands.update_order import UpdateOrder
from src.models.order import Order
from src.models.order_item import OrderItem
from src.models.customer import Customer
from src.errors.errors import ValidationError, NotFoundError, ApiError, DatabaseError


class TestUpdateOrder90Coverage:
    """Tests para alcanzar 90% de cobertura en update_order.py"""
    
    def test_update_order_status_field_not_string(self, db, sample_order):
        """Test validación de status que no es string (línea 166)."""
        update_data = {
            'status': 123  # Número en lugar de string
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "must be a string" in str(exc_info.value).lower()
    
    def test_update_order_numeric_field_not_string(self, db, sample_order):
        """Test validación de campos numéricos que no son strings (línea 176)."""
        update_data = {
            'delivery_city': 12345  # Número en lugar de string
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "must be a string" in str(exc_info.value).lower()
    
    def test_update_order_items_not_list(self, db, sample_order):
        """Test validación de items que no es lista (línea 189)."""
        update_data = {
            'items': 'not_a_list'  # String en lugar de lista
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "must be a list" in str(exc_info.value).lower()
    
    def test_update_order_item_not_dict(self, db, sample_order):
        """Test validación de item que no es diccionario (línea 196)."""
        update_data = {
            'items': [
                'not_a_dict'  # String en lugar de dict
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "must be a valid object" in str(exc_info.value).lower()
    
    def test_update_order_item_quantity_type_error(self, db, sample_order):
        """Test error de tipo en quantity (línea 212)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 'abc',  # No se puede convertir a int
                    'unit_price': 1000.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid integer" in str(exc_info.value).lower()
    
    def test_update_order_item_unit_price_type_error(self, db, sample_order):
        """Test error de tipo en unit_price (línea 220)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 'invalid_price'  # No se puede convertir a float
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_item_discount_type_error(self, db, sample_order):
        """Test error de tipo en discount_percentage (línea 228)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'discount_percentage': 'invalid_discount'  # No se puede convertir a float
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_item_tax_negative_validation(self, db, sample_order):
        """Test validación de tax_percentage negativo (línea 367)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'tax_percentage': -5  # Negativo
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "cannot be negative" in str(exc_info.value).lower() or "0" in str(exc_info.value)
    
    def test_update_order_item_tax_type_error(self, db, sample_order):
        """Test error de tipo en tax_percentage (línea 369-371)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'tax_percentage': 'invalid_tax'  # No se puede convertir a float
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_item_product_sku_empty(self, db, sample_order):
        """Test validación de product_sku vacío (línea 378-380)."""
        update_data = {
            'items': [
                {
                    'product_sku': '',  # SKU vacío
                    'quantity': 5,
                    'unit_price': 1000.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "cannot be empty" in str(exc_info.value).lower()
    
    def test_update_order_item_product_sku_whitespace(self, db, sample_order):
        """Test validación de product_sku solo con espacios (línea 378-380)."""
        update_data = {
            'items': [
                {
                    'product_sku': '   ',  # Solo espacios
                    'quantity': 5,
                    'unit_price': 1000.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "cannot be empty" in str(exc_info.value).lower()
    
    def test_update_order_item_quantity_value_error_in_validate(self, db, sample_order):
        """Test ValueError al validar quantity en _validate_item_data (línea 350-352)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': None,  # None no se puede convertir a int
                    'unit_price': 1000.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid" in str(exc_info.value).lower() and "integer" in str(exc_info.value).lower()
    
    def test_update_order_item_unit_price_value_error_in_validate(self, db, sample_order):
        """Test ValueError al validar unit_price en _validate_item_data (línea 358-360)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': None  # None no se puede convertir a float
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_item_discount_value_error_in_validate(self, db, sample_order):
        """Test ValueError al validar discount en _validate_item_data (línea 369-371)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'discount_percentage': [10, 20]  # Lista no se puede convertir a float
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_item_tax_value_error_in_validate(self, db, sample_order):
        """Test ValueError al validar tax en _validate_item_data (línea 378-380)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'tax_percentage': {'rate': 19}  # Dict no se puede convertir a float
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_item_value_error_creating_item(self, db, sample_order):
        """Test ValueError/TypeError al crear item (línea 325)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'discount_percentage': 10.0,
                    'tax_percentage': 'not_a_valid_tax'  # Pasará validación inicial pero fallará en Decimal
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        # Este test debe capturar la validación
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid number" in str(exc_info.value).lower()
    
    def test_update_order_sqlalchemy_error_creating_item(self, db, sample_order, monkeypatch):
        """Test SQLAlchemyError al crear item (línea 327)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0
                }
            ]
        }
        
        # Mock db.session.add para que lance SQLAlchemyError
        original_add = db.session.add
        
        def mock_add(obj):
            if isinstance(obj, OrderItem):
                raise SQLAlchemyError("Database error creating item")
            return original_add(obj)
        
        monkeypatch.setattr(db.session, 'add', mock_add)
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(DatabaseError) as exc_info:
            command.execute()
        
        assert "error creating item" in str(exc_info.value).lower()
    
    def test_update_order_status_transition_delivered_to_pending(self, db, sample_order):
        """Test transición inválida de delivered a pending (línea 288, 291)."""
        # Cambiar el estado a delivered primero
        sample_order.status = 'delivered'
        db.session.commit()
        
        update_data = {
            'status': 'pending'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        # Esperamos un ApiError porque solo se pueden editar órdenes pendientes
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        assert "pendiente" in str(exc_info.value).lower()
    
    def test_update_order_recalculate_with_items(self, db, sample_order):
        """Test recálculo de totales con items (líneas 404-408)."""
        # Crear items con descuentos y taxes para probar el cálculo completo
        update_data = {
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Product 1',
                    'quantity': 10,
                    'unit_price': 100.0,
                    'discount_percentage': 10.0,  # 10% descuento
                    'tax_percentage': 19.0  # 19% IVA
                },
                {
                    'product_sku': 'PROD-002',
                    'product_name': 'Product 2',
                    'quantity': 5,
                    'unit_price': 200.0,
                    'discount_percentage': 5.0,  # 5% descuento
                    'tax_percentage': 19.0  # 19% IVA
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verificar que los totales se calcularon correctamente
        # Item 1: 10 * 100 = 1000, descuento 100 = 900, tax 171 = 1071
        # Item 2: 5 * 200 = 1000, descuento 50 = 950, tax 180.5 = 1130.5
        # Subtotal: 2000
        # Descuento total: 150
        # Tax total: 351.5
        # Total: 2201.5
        
        assert result['subtotal'] == 2000.0
        assert result['discount_amount'] == 150.0
        assert result['tax_amount'] == 351.5
        assert result['total_amount'] == 2201.5
    
    def test_update_order_payment_terms_field_validation(self, db, sample_order):
        """Test validación de payment_terms como string (línea 176)."""
        update_data = {
            'payment_terms': ['not', 'a', 'string']  # Lista en lugar de string
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "must be a string" in str(exc_info.value).lower()
    
    def test_update_order_notes_field_validation(self, db, sample_order):
        """Test validación de notes como string (línea 176)."""
        update_data = {
            'notes': {'text': 'This is a note'}  # Dict en lugar de string
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "must be a string" in str(exc_info.value).lower()
    
    def test_update_order_data_not_dict(self, db, sample_order):
        """Test validación de order_data que no es dict (línea 160)."""
        update_data = "not a dictionary"  # String en lugar de dict
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "valid json object" in str(exc_info.value).lower()
    
    def test_update_order_item_discount_negative_in_validate(self, db, sample_order):
        """Test validación de discount negativo en _validate_item_data (línea 367)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'discount_percentage': -10.0  # Negativo
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "cannot be negative" in str(exc_info.value).lower() or "between 0 and 100" in str(exc_info.value).lower()
    
    def test_update_order_item_discount_over_100_in_validate(self, db, sample_order):
        """Test validación de discount > 100 en _validate_item_data (línea 369-371)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'JER-001',
                    'quantity': 5,
                    'unit_price': 1000.0,
                    'discount_percentage': 150.0  # Mayor a 100
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        with pytest.raises(ValidationError) as exc_info:
            command.execute()
        
        assert "exceed 100" in str(exc_info.value).lower() or "between 0 and 100" in str(exc_info.value).lower()
    
    def test_update_order_status_confirmed_to_pending(self, db, sample_order):
        """Test transición inválida de confirmed a pending - debe fallar por reglas de negocio."""
        # Cambiar el estado a confirmed primero
        sample_order.status = 'confirmed'
        db.session.commit()
        
        update_data = {
            'status': 'pending'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        
        # Esperamos un ApiError porque confirmed no puede volver a pending
        with pytest.raises(ApiError) as exc_info:
            command.execute()
        
        # El error debe mencionar que la transición es inválida
        assert "transition" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
    
    def test_update_order_with_tax_and_discount_calculations(self, db, sample_order):
        """Test para cubrir todas las líneas del recálculo (404-408)."""
        update_data = {
            'items': [
                {
                    'product_sku': 'PROD-001',
                    'product_name': 'Product 1',
                    'quantity': 1,
                    'unit_price': 1000.0,
                    'discount_percentage': 20.0,
                    'tax_percentage': 10.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verificar cálculos:
        # Subtotal: 1 * 1000 = 1000
        # Descuento: 1000 * 0.20 = 200
        # Base imponible: 1000 - 200 = 800
        # Tax: 800 * 0.10 = 80
        # Total: 1000 - 200 + 80 = 880
        
        assert result['subtotal'] == 1000.0
        assert result['discount_amount'] == 200.0
        assert result['tax_amount'] == 80.0
        assert result['total_amount'] == 880.0
