import json


class TestSuppliersBlueprint:

    def test_list_suppliers_empty(self, client):
        response = client.get('/suppliers')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'suppliers' in data

    def test_create_supplier_and_get(self, client):
        payload = {
            'name': 'Acme Supplies',
            'legal_name': 'Acme Supplies LLC',
            'tax_id': 'TAX-001',
            'country': 'Colombia'
        }

        r = client.post('/suppliers', json=payload)
        assert r.status_code == 201
        created = json.loads(r.data)
        assert created['name'] == payload['name']

        supplier_id = created['id']
        r2 = client.get(f'/suppliers/{supplier_id}')
        assert r2.status_code == 200
        got = json.loads(r2.data)
        assert got['id'] == supplier_id

    def test_update_supplier(self, client, sample_supplier):
        data = {'phone': '+57-300-0000000'}
        r = client.put(f'/suppliers/{sample_supplier.id}', json=data)
        assert r.status_code == 200
        updated = json.loads(r.data)
        assert updated['phone'] == data['phone']

    def test_delete_supplier_soft(self, client, sample_supplier):
        r = client.delete(f'/suppliers/{sample_supplier.id}')
        assert r.status_code == 200
        res = json.loads(r.data)
        assert res['deleted_supplier']['id'] == sample_supplier.id

        # Ensure supplier is inactive afterwards
        r2 = client.get(f'/suppliers/{sample_supplier.id}')
        assert r2.status_code == 200
        got = json.loads(r2.data)
        assert got['is_active'] is False
