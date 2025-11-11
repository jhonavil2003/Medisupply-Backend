import pytest
from src.commands.create_supplier import CreateSupplier
from src.commands.update_supplier import UpdateSupplier
from src.commands.get_supplier_by_id import GetSupplierById
from src.models.supplier import Supplier

class TestSupplierAddressBugFixes:
    """
    Tests específicos para verificar los bugs corregidos:
    1. Address fields anidados se persisten correctamente
    2. Currency permite valores null sin forzar USD
    """
    
    def test_create_supplier_with_nested_address_structure(self, app, db):
        """Test que el address anidado se mapea correctamente en CREATE"""
        payload = {
            'name': 'Test Address Bug',
            'legal_name': 'Test Address Bug S.A.',
            'tax_id': 'ADDR-001',
            'country': 'Colombia',
            'address': {
                'line1': 'Calle Nested 123',
                'city': 'Bogotá',
                'state': 'Cundinamarca',
                'country': 'Colombia',
                'postal_code': '110111'
            }
        }
        
        command = CreateSupplier(payload)
        result = command.execute()
        
        # Verificar que los campos de address anidados se guardaron
        assert result['address']['line1'] == 'Calle Nested 123'
        assert result['address']['city'] == 'Bogotá' 
        assert result['address']['state'] == 'Cundinamarca'
        assert result['address']['country'] == 'Colombia'
        assert result['address']['postal_code'] == '110111'
        
        # Verificar en la base de datos
        supplier = db.session.query(Supplier).filter_by(tax_id='ADDR-001').first()
        assert supplier.address_line1 == 'Calle Nested 123'
        assert supplier.city == 'Bogotá'
        assert supplier.state == 'Cundinamarca'
        assert supplier.postal_code == '110111'

    def test_create_supplier_with_currency_null(self, app, db):
        """Test que currency null no se fuerza a USD"""
        payload = {
            'name': 'Test Currency Null',
            'legal_name': 'Test Currency Null S.A.',
            'tax_id': 'CURR-001',
            'country': 'Colombia',
            'currency': None  # Explicitly null
        }
        
        command = CreateSupplier(payload)
        result = command.execute()
        
        # Verificar que currency es null, no "USD"
        assert result['currency'] is None
        
        # Verificar en la base de datos
        supplier = db.session.query(Supplier).filter_by(tax_id='CURR-001').first()
        assert supplier.currency is None

    def test_update_supplier_with_nested_address_structure(self, app, db):
        """Test que UPDATE maneja correctamente el address anidado"""
        # Crear supplier inicial
        initial_payload = {
            'name': 'Test Update Address',
            'legal_name': 'Test Update Address S.A.',
            'tax_id': 'UPD-ADDR-001', 
            'country': 'Colombia'
        }
        
        create_command = CreateSupplier(initial_payload)
        created = create_command.execute()
        supplier_id = created['id']
        
        # Actualizar con address anidado
        update_payload = {
            'address': {
                'line1': 'Dirección Actualizada 456',
                'city': 'Medellín',
                'state': 'Antioquia',
                'country': 'Colombia'
            }
        }
        
        update_command = UpdateSupplier(supplier_id, update_payload)
        result = update_command.execute()
        
        # Verificar que los campos se actualizaron
        assert result['address']['line1'] == 'Dirección Actualizada 456'
        assert result['address']['city'] == 'Medellín'
        assert result['address']['state'] == 'Antioquia'
        
        # Verificar en la base de datos
        supplier = db.session.query(Supplier).filter_by(id=supplier_id).first()
        assert supplier.address_line1 == 'Dirección Actualizada 456'
        assert supplier.city == 'Medellín'
        assert supplier.state == 'Antioquia'

    def test_update_supplier_currency_to_null(self, app, db):
        """Test que UPDATE permite cambiar currency a null"""
        # Crear supplier con currency específico
        initial_payload = {
            'name': 'Test Currency Update',
            'legal_name': 'Test Currency Update S.A.',
            'tax_id': 'UPD-CURR-001',
            'country': 'Colombia',
            'currency': 'COP'
        }
        
        create_command = CreateSupplier(initial_payload)
        created = create_command.execute()
        supplier_id = created['id']
        
        # Actualizar currency a null
        update_payload = {'currency': None}
        
        update_command = UpdateSupplier(supplier_id, update_payload)
        result = update_command.execute()
        
        # Verificar que currency es null
        assert result['currency'] is None
        
        # Verificar en la base de datos
        supplier = db.session.query(Supplier).filter_by(id=supplier_id).first()
        assert supplier.currency is None

    def test_backward_compatibility_flat_address_structure(self, app, db):
        """Test que la estructura plana de address sigue funcionando (backward compatibility)"""
        payload = {
            'name': 'Test Flat Address',
            'legal_name': 'Test Flat Address S.A.',
            'tax_id': 'FLAT-001',
            'country': 'Colombia',
            'address_line1': 'Calle Plana 789',
            'city': 'Cali',
            'state': 'Valle del Cauca'
        }
        
        command = CreateSupplier(payload)
        result = command.execute()
        
        # Verificar que los campos planos se guardaron
        assert result['address']['line1'] == 'Calle Plana 789'
        assert result['address']['city'] == 'Cali'
        assert result['address']['state'] == 'Valle del Cauca'

    def test_mixed_nested_and_flat_address_priority(self, app, db):
        """Test que la estructura anidada tiene prioridad sobre la plana"""
        payload = {
            'name': 'Test Mixed Address',
            'legal_name': 'Test Mixed Address S.A.',
            'tax_id': 'MIX-001',
            'country': 'Colombia',
            # Estructura anidada
            'address': {
                'line1': 'Nested Line 1',
                'city': 'Nested City'
            },
            # Estructura plana (debería ser ignorada)
            'address_line1': 'Flat Line 1',
            'city': 'Flat City'
        }
        
        command = CreateSupplier(payload)
        result = command.execute()
        
        # Verificar que los valores anidados tienen prioridad
        assert result['address']['line1'] == 'Nested Line 1'
        assert result['address']['city'] == 'Nested City'