import pytest
import json
from datetime import date


class TestSalespersonsBlueprint:
    """Test cases for salespersons blueprint endpoints"""
    
    def test_get_salespersons_all(self, client, sample_salesperson):
        """Test GET /salespersons without filters."""
        response = client.get('/salespersons/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'salespersons' in data
        assert 'total' in data
        assert data['total'] >= 1
        assert isinstance(data['salespersons'], list)
        
        # Check first salesperson structure
        salesperson = data['salespersons'][0]
        assert 'id' in salesperson
        assert 'employee_id' in salesperson
        assert 'first_name' in salesperson
        assert 'last_name' in salesperson
        assert 'email' in salesperson
        assert 'is_active' in salesperson
    
    def test_get_salespersons_active_filter(self, client, multiple_salespersons):
        """Test GET /salespersons filtered by is_active."""
        response = client.get('/salespersons/?is_active=true')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 2  # At least 2 active salespersons
        assert all(sp['is_active'] is True for sp in data['salespersons'])
    
    def test_get_salespersons_inactive_filter(self, client, multiple_salespersons):
        """Test GET /salespersons filtered by is_active=false."""
        response = client.get('/salespersons/?is_active=false')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should find at least one inactive salesperson
        if data['total'] > 0:
            assert all(sp['is_active'] is False for sp in data['salespersons'])
    
    def test_get_salespersons_territory_filter(self, client, sample_salesperson):
        """Test GET /salespersons filtered by territory."""
        territory = sample_salesperson.territory
        response = client.get(f'/salespersons/?territory={territory}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        if data['total'] > 0:
            assert all(sp['territory'] == territory for sp in data['salespersons'])
    
    def test_get_salesperson_by_id(self, client, sample_salesperson):
        """Test GET /salespersons/<id> - retrieve single salesperson."""
        response = client.get(f'/salespersons/{sample_salesperson.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_salesperson.id
        assert data['employee_id'] == sample_salesperson.employee_id
        assert data['first_name'] == sample_salesperson.first_name
        assert data['last_name'] == sample_salesperson.last_name
        assert data['email'] == sample_salesperson.email
        assert data['full_name'] == sample_salesperson.get_full_name()
        assert 'territory' in data
        assert 'is_active' in data
    
    def test_get_salesperson_by_id_not_found(self, client):
        """Test GET /salespersons/<id> with non-existent ID."""
        response = client.get('/salespersons/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_salesperson_success(self, client):
        """Test POST /salespersons/ - create new salesperson successfully."""
        salesperson_data = {
            'employee_id': 'SELLER-NEW-001',
            'first_name': 'Nuevo',
            'last_name': 'Vendedor',
            'email': 'nuevo.vendedor@medisupply.com',
            'phone': '+57 300 5555555',
            'territory': 'Cartagena',
            'hire_date': '2025-01-15',
            'is_active': True
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'salesperson' in data
        assert data['salesperson']['employee_id'] == 'SELLER-NEW-001'
        assert data['salesperson']['first_name'] == 'Nuevo'
        assert data['salesperson']['last_name'] == 'Vendedor'
        assert data['salesperson']['email'] == 'nuevo.vendedor@medisupply.com'
        assert data['salesperson']['is_active'] is True
    
    def test_create_salesperson_minimal_data(self, client):
        """Test creating salesperson with only required fields."""
        salesperson_data = {
            'employee_id': 'SELLER-MINIMAL-001',
            'first_name': 'Min',
            'last_name': 'User',
            'email': 'min.user@medisupply.com'
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['salesperson']['employee_id'] == 'SELLER-MINIMAL-001'
        assert data['salesperson']['is_active'] is True  # Default value
    
    def test_create_salesperson_missing_required_fields(self, client):
        """Test creating salesperson with missing required fields."""
        # Missing employee_id
        salesperson_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@medisupply.com'
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_salesperson_duplicate_employee_id(self, client, sample_salesperson):
        """Test creating salesperson with duplicate employee_id."""
        salesperson_data = {
            'employee_id': sample_salesperson.employee_id,  # Duplicate
            'first_name': 'Duplicate',
            'last_name': 'Test',
            'email': 'duplicate@medisupply.com'
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_salesperson_duplicate_email(self, client, sample_salesperson):
        """Test creating salesperson with duplicate email."""
        salesperson_data = {
            'employee_id': 'SELLER-DUP-EMAIL-001',
            'first_name': 'Duplicate',
            'last_name': 'Email',
            'email': sample_salesperson.email  # Duplicate email
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_salesperson_success(self, client, sample_salesperson):
        """Test PUT /salespersons/<id> - update salesperson successfully."""
        update_data = {
            'first_name': 'Updated Juan',
            'last_name': 'Updated Pérez',
            'phone': '+57 301 9999999',
            'territory': 'Bogotá Sur'
        }
        
        response = client.put(f'/salespersons/{sample_salesperson.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['salesperson']['first_name'] == 'Updated Juan'
        assert data['salesperson']['last_name'] == 'Updated Pérez'
        assert data['salesperson']['phone'] == '+57 301 9999999'
        assert data['salesperson']['territory'] == 'Bogotá Sur'
        # Should update full_name automatically
        assert data['salesperson']['full_name'] == 'Updated Juan Updated Pérez'
    
    def test_update_salesperson_not_found(self, client):
        """Test updating non-existent salesperson."""
        update_data = {
            'first_name': 'Updated Name'
        }
        
        response = client.put('/salespersons/99999',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 404
    
    def test_update_salesperson_duplicate_employee_id(self, client, sample_salesperson, sample_salesperson_2):
        """Test updating salesperson with existing employee_id."""
        update_data = {
            'employee_id': sample_salesperson_2.employee_id  # Use other's ID
        }
        
        response = client.put(f'/salespersons/{sample_salesperson.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_salesperson_duplicate_email(self, client, sample_salesperson, sample_salesperson_2):
        """Test updating salesperson with existing email."""
        update_data = {
            'email': sample_salesperson_2.email  # Use other's email
        }
        
        response = client.put(f'/salespersons/{sample_salesperson.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_delete_salesperson_success(self, client, sample_salesperson_2):
        """Test DELETE /salespersons/<id> - delete salesperson without visits."""
        salesperson_id = sample_salesperson_2.id
        
        response = client.delete(f'/salespersons/{salesperson_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        
        # Verify salesperson is actually deleted
        get_response = client.get(f'/salespersons/{salesperson_id}')
        assert get_response.status_code == 404
    
    def test_delete_salesperson_with_visits(self, client, sample_salesperson, sample_visit):
        """Test deleting salesperson that has associated visits."""
        response = client.delete(f'/salespersons/{sample_salesperson.id}')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        # Should mention that salesperson has visits
    
    def test_delete_salesperson_not_found(self, client):
        """Test deleting non-existent salesperson."""
        response = client.delete('/salespersons/99999')
        
        assert response.status_code == 404
    
    def test_salesperson_to_dict_includes_full_name(self, client, sample_salesperson):
        """Test that API responses include computed full_name field."""
        response = client.get(f'/salespersons/{sample_salesperson.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'full_name' in data
        assert data['full_name'] == f"{sample_salesperson.first_name} {sample_salesperson.last_name}"
    
    def test_salesperson_date_serialization(self, client):
        """Test that dates are properly serialized in API responses."""
        salesperson_data = {
            'employee_id': 'SELLER-DATE-001',
            'first_name': 'Date',
            'last_name': 'Test',
            'email': 'date.test@medisupply.com',
            'hire_date': '2023-06-15'
        }
        
        # Create salesperson
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['salesperson']['hire_date'] == '2023-06-15'
    
    def test_salesperson_null_optional_fields(self, client):
        """Test handling of null optional fields."""
        salesperson_data = {
            'employee_id': 'SELLER-NULL-001',
            'first_name': 'Null',
            'last_name': 'Test',
            'email': 'null.test@medisupply.com'
            # phone, territory, hire_date not provided
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['salesperson']['phone'] is None
        assert data['salesperson']['territory'] is None
        assert data['salesperson']['hire_date'] is None
    
    def test_salespersons_pagination_structure(self, client, multiple_salespersons):
        """Test that salespersons endpoint returns properly structured data."""
        response = client.get('/salespersons/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data
        assert 'salespersons' in data
        assert isinstance(data['total'], int)
        assert isinstance(data['salespersons'], list)
        assert data['total'] >= 3  # We have multiple_salespersons fixture
    
    def test_salesperson_boolean_fields(self, client):
        """Test proper handling of boolean fields."""
        # Create inactive salesperson
        salesperson_data = {
            'employee_id': 'SELLER-INACTIVE-001',
            'first_name': 'Inactive',
            'last_name': 'User',
            'email': 'inactive@medisupply.com',
            'is_active': False
        }
        
        response = client.post('/salespersons/',
                              data=json.dumps(salesperson_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['salesperson']['is_active'] is False
        
        # Update to active
        update_data = {'is_active': True}
        response = client.put(f'/salespersons/{data["salesperson"]["id"]}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['salesperson']['is_active'] is True