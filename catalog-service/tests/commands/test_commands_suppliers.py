import pytest
from src.commands.create_supplier import CreateSupplier
from src.commands.get_supplier_by_id import GetSupplierById
from src.commands.update_supplier import UpdateSupplier
from src.commands.delete_supplier import DeleteSupplier
from src.errors.errors import ValidationError, NotFoundError


class TestSupplierCommands:

    def test_create_supplier_validation(self, db):
        # Missing required fields
        with pytest.raises(ValidationError):
            CreateSupplier({}).execute()

    def test_create_and_get_supplier(self, db):
        data = {'name': 'Acme', 'legal_name': 'Acme LLC', 'tax_id': 'TAX-123', 'country': 'USA'}
        created = CreateSupplier(data).execute()
        assert 'id' in created

        got = GetSupplierById(created['id']).execute()
        assert got['tax_id'] == data['tax_id']

    def test_update_supplier_not_found(self, db):
        with pytest.raises(NotFoundError):
            UpdateSupplier(99999, {'name': 'x'}).execute()

    def test_delete_supplier_not_found(self, db):
        with pytest.raises(NotFoundError):
            DeleteSupplier(99999).execute()
