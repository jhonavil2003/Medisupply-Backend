"""Lightweight test runner for suppliers features that does not require pytest.

Run with the project's Python (for example, after activating .venv):

    source .venv/bin/activate
    python3 catalog-service/run_supplier_tests.py

This script sets up an in-memory SQLite database, registers the app,
and runs a few basic assertions covering the commands and blueprint
endpoints added for suppliers.
"""
import sys
import os
from decimal import Decimal

# Ensure src is importable
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'src'))

def abort(msg):
    print('FAILED:', msg)
    sys.exit(1)

try:
    from src.main import create_app
    from src.session import db
    from src.models.supplier import Supplier
    from src.commands.create_supplier import CreateSupplier
    from src.commands.get_supplier_by_id import GetSupplierById
    from src.commands.update_supplier import UpdateSupplier
    from src.commands.delete_supplier import DeleteSupplier
except Exception as e:
    abort(f'Import error: {e}')


def run():
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    }

    app = create_app(config=config)

    with app.app_context():
        db.create_all()

        print('DB created')

        # Command-level: create supplier
        data = {'name': 'Runner Supplier', 'legal_name': 'Runner LLC', 'tax_id': 'RUN-001', 'country': 'Testland'}
        created = CreateSupplier(data).execute()
        assert created['name'] == data['name'], 'CreateSupplier returned wrong name'
        sid = created['id']
        print('CreateSupplier OK, id=', sid)

        # Get by id
        got = GetSupplierById(sid).execute()
        assert got['tax_id'] == data['tax_id'], 'GetSupplierById failed'
        print('GetSupplierById OK')

        # Update
        upd = UpdateSupplier(sid, {'phone': '+57-300-0000000'}).execute()
        assert upd['phone'] == '+57-300-0000000', 'UpdateSupplier failed'
        print('UpdateSupplier OK')

        # Soft delete
        res = DeleteSupplier(sid).execute()
        assert res['deleted_supplier']['id'] == sid, 'DeleteSupplier response wrong'
        print('DeleteSupplier OK')

        # Ensure supplier is inactive in DB
        s = Supplier.query.get(sid)
        assert s is not None, 'Supplier disappeared after delete'
        assert s.is_active is False, 'Supplier not marked inactive'
        print('Soft-delete persisted OK')

        # Blueprint-level check using test client
        client = app.test_client()

        # Create via endpoint
        payload = {'name': 'HTTP Supplier', 'legal_name': 'HTTP LLC', 'tax_id': 'HTTP-001', 'country': 'Nowhere'}
        r = client.post('/suppliers', json=payload)
        assert r.status_code == 201, f'POST /suppliers failed: {r.status_code} {r.data}'
        created_http = r.get_json()
        hid = created_http['id']
        print('POST /suppliers OK id=', hid)

        # Get via endpoint
        r2 = client.get(f'/suppliers/{hid}')
        assert r2.status_code == 200, 'GET /suppliers/<id> failed'
        print('GET /suppliers/<id> OK')

        # Update via endpoint
        r3 = client.put(f'/suppliers/{hid}', json={'phone': '+57-111-2222'})
        assert r3.status_code == 200, 'PUT /suppliers/<id> failed'
        print('PUT /suppliers/<id> OK')

        # Delete via endpoint
        r4 = client.delete(f'/suppliers/{hid}')
        assert r4.status_code == 200, 'DELETE /suppliers/<id> failed'
        print('DELETE /suppliers/<id> OK')

        print('\nAll supplier checks passed ✅')


if __name__ == '__main__':
    run()
