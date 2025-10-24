import pytest
from src.commands.update_order import UpdateOrder


class TestAutoConfirmOrder:
    """Test que verifica el cambio automático de estado PENDING → CONFIRMED."""
    
    def test_update_auto_confirms_pending_order(self, db, sample_order):
        """Test que al actualizar una orden PENDING, automáticamente cambia a CONFIRMED."""
        # Verify order starts as pending
        assert sample_order.status == 'pending'
        
        # Update order with simple field
        update_data = {
            'notes': 'Orden actualizada - debe auto-confirmar'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        # Verify status changed to confirmed automatically
        assert result['status'] == 'confirmed'
        assert result['notes'] == 'Orden actualizada - debe auto-confirmar'
    
    def test_update_with_delivery_address_auto_confirms(self, db, sample_order):
        """Test que actualizar dirección también auto-confirma."""
        assert sample_order.status == 'pending'
        
        update_data = {
            'delivery_address': 'Nueva Calle 456 #78-90',
            'delivery_city': 'Medellín'
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        assert result['status'] == 'confirmed'
        assert result['delivery_address'] == 'Nueva Calle 456 #78-90'
    
    def test_update_with_items_auto_confirms(self, db, sample_order):
        """Test que actualizar items también auto-confirma."""
        assert sample_order.status == 'pending'
        
        update_data = {
            'items': [
                {
                    'product_sku': 'NEW-SKU-001',
                    'product_name': 'Nuevo Producto',
                    'quantity': 50,
                    'unit_price': 2000.0,
                    'discount_percentage': 0.0,
                    'tax_percentage': 19.0
                }
            ]
        }
        
        command = UpdateOrder(sample_order.id, update_data)
        result = command.execute()
        
        assert result['status'] == 'confirmed'
        assert len(result['items']) == 1
        assert result['items'][0]['product_sku'] == 'NEW-SKU-001'
