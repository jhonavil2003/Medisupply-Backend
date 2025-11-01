import pytest
import json
from datetime import date, time
from decimal import Decimal
from src.entities.visit_status import VisitStatus


class TestVisitsBlueprint:
    """Test cases for visits blueprint endpoints"""
    
    def test_get_visits_all(self, client, sample_visit):
        """Test GET /visits without filters."""
        response = client.get('/visits/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'visits' in data
        assert 'total' in data
        assert data['total'] >= 1
        assert isinstance(data['visits'], list)
        assert len(data['visits']) >= 1
        
        # Check first visit structure
        visit = data['visits'][0]
        assert 'id' in visit
        assert 'customer_id' in visit
        assert 'salesperson_id' in visit
        assert 'status' in visit
    
    def test_get_visits_by_customer(self, client, sample_visit):
        """Test GET /visits filtered by customer_id."""
        response = client.get(f'/visits/?customer_id={sample_visit.customer_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(visit['customer_id'] == sample_visit.customer_id for visit in data['visits'])
    
    def test_get_visits_by_salesperson(self, client, sample_visit):
        """Test GET /visits filtered by salesperson_id.""" 
        response = client.get(f'/visits/?salesperson_id={sample_visit.salesperson_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(visit['salesperson_id'] == sample_visit.salesperson_id for visit in data['visits'])
    
    def test_get_visits_by_status(self, client, sample_visit):
        """Test GET /visits filtered by status."""
        response = client.get('/visits/?status=PROGRAMADA')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] >= 1
        assert all(visit['status'] == 'PROGRAMADA' for visit in data['visits'])
    
    def test_get_visits_combined_filters(self, client, sample_visit):
        """Test GET /visits with multiple filters."""
        url = f'/visits/?customer_id={sample_visit.customer_id}&status=PROGRAMADA'
        response = client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        if data['total'] > 0:
            for visit in data['visits']:
                assert visit['customer_id'] == sample_visit.customer_id
                assert visit['status'] == 'PROGRAMADA'
    
    def test_get_visit_by_id(self, client, sample_visit):
        """Test GET /visits/<id> - retrieve single visit."""
        response = client.get(f'/visits/{sample_visit.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == sample_visit.id
        assert data['customer_id'] == sample_visit.customer_id
        assert data['salesperson_id'] == sample_visit.salesperson_id
        assert data['status'] == sample_visit.status.value
        assert 'visit_date' in data
        assert 'visit_time' in data
    
    def test_get_visit_by_id_not_found(self, client):
        """Test GET /visits/<id> with non-existent ID."""
        response = client.get('/visits/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_visit_success(self, client, sample_customer, sample_salesperson):
        """Test POST /visits/ - create new visit successfully."""
        visit_data = {
            'customer_id': sample_customer.id,
            'salesperson_id': sample_salesperson.id,
            'visit_date': '2025-12-15',
            'visit_time': '14:30:00',
            'contacted_persons': 'Dr. Test Person',
            'clinical_findings': 'Test findings',
            'additional_notes': 'Test notes',
            'address': 'Test Address 123',
            'latitude': 4.60971,
            'longitude': -74.08175
        }
        
        response = client.post('/visits/', 
                              data=json.dumps(visit_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'visit' in data
        assert data['visit']['customer_id'] == sample_customer.id
        assert data['visit']['salesperson_id'] == sample_salesperson.id
        assert data['visit']['status'] == 'PROGRAMADA'  # Default status
        assert data['visit']['contacted_persons'] == 'Dr. Test Person'
    
    def test_create_visit_minimal_data(self, client, sample_customer, sample_salesperson):
        """Test creating visit with only required fields."""
        visit_data = {
            'customer_id': sample_customer.id,
            'salesperson_id': sample_salesperson.id,
            'visit_date': '2025-12-20',
            'visit_time': '09:00:00'
        }
        
        response = client.post('/visits/',
                              data=json.dumps(visit_data), 
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['visit']['customer_id'] == sample_customer.id
        assert data['visit']['salesperson_id'] == sample_salesperson.id
        assert data['visit']['status'] == 'PROGRAMADA'
    
    def test_create_visit_missing_required_fields(self, client):
        """Test creating visit with missing required fields."""
        # Missing customer_id
        visit_data = {
            'salesperson_id': 1,
            'visit_date': '2025-12-25',
            'visit_time': '10:00:00'
        }
        
        response = client.post('/visits/',
                              data=json.dumps(visit_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_visit_invalid_date_format(self, client, sample_customer, sample_salesperson):
        """Test creating visit with invalid date format."""
        visit_data = {
            'customer_id': sample_customer.id,
            'salesperson_id': sample_salesperson.id,
            'visit_date': 'invalid-date',
            'visit_time': '10:00:00'
        }
        
        response = client.post('/visits/',
                              data=json.dumps(visit_data),
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_update_visit_success(self, client, sample_visit):
        """Test PUT /visits/<id> - update visit successfully."""
        update_data = {
            'contacted_persons': 'Updated Contact Person',
            'clinical_findings': 'Updated findings',
            'additional_notes': 'Updated notes'
        }
        
        response = client.put(f'/visits/{sample_visit.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['visit']['contacted_persons'] == 'Updated Contact Person'
        assert data['visit']['clinical_findings'] == 'Updated findings'
        assert data['visit']['additional_notes'] == 'Updated notes'
        # Status should remain the same (ignored in update)
        assert data['visit']['status'] == sample_visit.status.value
    
    def test_update_visit_not_found(self, client):
        """Test updating non-existent visit."""
        update_data = {
            'additional_notes': 'Updated notes'
        }
        
        response = client.put('/visits/99999',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 404
    
    def test_delete_visit_success(self, client, sample_visit):
        """Test DELETE /visits/<id> - physical deletion."""
        visit_id = sample_visit.id
        
        response = client.delete(f'/visits/{visit_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        
        # Verify visit is actually deleted
        get_response = client.get(f'/visits/{visit_id}')
        assert get_response.status_code == 404
    
    def test_delete_visit_not_found(self, client):
        """Test deleting non-existent visit."""
        response = client.delete('/visits/99999')
        
        assert response.status_code == 404
    
    def test_get_visits_by_salesperson_route(self, client, sample_visit):
        """Test GET /visits/salesperson/<id>."""
        response = client.get(f'/visits/salesperson/{sample_visit.salesperson_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'visits' in data
        assert isinstance(data['visits'], list)
        if len(data['visits']) > 0:
            assert all(visit['salesperson_id'] == sample_visit.salesperson_id for visit in data['visits'])
    
    def test_get_visits_by_customer_route(self, client, sample_visit):
        """Test GET /visits/customer/<id>."""
        response = client.get(f'/visits/customer/{sample_visit.customer_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'visits' in data
        assert isinstance(data['visits'], list)
        if len(data['visits']) > 0:
            assert all(visit['customer_id'] == sample_visit.customer_id for visit in data['visits'])
    
    def test_get_visits_by_status_route(self, client, multiple_visits):
        """Test GET /visits/status/<status>."""
        response = client.get('/visits/status/PROGRAMADA')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'visits' in data
        assert isinstance(data['visits'], list)
        assert all(visit['status'] == 'PROGRAMADA' for visit in data['visits'])
    
    def test_complete_visit_success(self, client, sample_visit):
        """Test POST /visits/<id>/complete - mark visit as completed."""
        # Ensure visit is PROGRAMADA
        sample_visit.status = VisitStatus.PROGRAMADA
        from src.session import db
        db.session.commit()
        
        response = client.post(f'/visits/{sample_visit.id}/complete')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert data['visit']['status'] == 'COMPLETADA'
    
    def test_complete_visit_invalid_status(self, client, sample_visit):
        """Test completing visit that's not in PROGRAMADA status."""
        # Set visit to COMPLETADA first
        sample_visit.status = VisitStatus.COMPLETADA
        from src.session import db
        db.session.commit()
        
        response = client.post(f'/visits/{sample_visit.id}/complete')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_mark_visit_deleted_success(self, client, sample_visit):
        """Test POST /visits/<id>/mark-deleted - mark visit as deleted."""
        response = client.post(f'/visits/{sample_visit.id}/mark-deleted')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert data['visit']['status'] == 'ELIMINADA'
    
    def test_mark_visit_deleted_not_found(self, client):
        """Test marking non-existent visit as deleted."""
        response = client.post('/visits/99999/mark-deleted')
        
        assert response.status_code == 404
    
    def test_visits_with_multiple_statuses(self, client, multiple_visits):
        """Test querying visits with different statuses."""
        # Test each status
        for status in ['PROGRAMADA', 'COMPLETADA', 'ELIMINADA']:
            response = client.get(f'/visits/?status={status}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'visits' in data
            # All returned visits should have the requested status
            for visit in data['visits']:
                assert visit['status'] == status
    
    def test_visits_pagination_like_behavior(self, client, multiple_visits):
        """Test that visits endpoint returns properly structured data."""
        response = client.get('/visits/')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total' in data
        assert 'visits' in data
        assert isinstance(data['total'], int)
        assert isinstance(data['visits'], list)
        assert data['total'] == len(data['visits'])  # In memory DB, should match
    
    def test_create_visit_ignores_status_field(self, client, sample_customer, sample_salesperson):
        """Test that status field is ignored during creation (always PROGRAMADA)."""
        visit_data = {
            'customer_id': sample_customer.id,
            'salesperson_id': sample_salesperson.id,
            'visit_date': '2025-12-30',
            'visit_time': '16:00:00',
            'status': 'COMPLETADA'  # This should be ignored
        }
        
        response = client.post('/visits/',
                              data=json.dumps(visit_data),
                              content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        # Status should be PROGRAMADA regardless of what was sent
        assert data['visit']['status'] == 'PROGRAMADA'
    
    def test_update_visit_ignores_status_field(self, client, sample_visit):
        """Test that status field is ignored during update."""
        original_status = sample_visit.status.value
        
        update_data = {
            'additional_notes': 'Updated notes',
            'status': 'COMPLETADA'  # This should be ignored
        }
        
        response = client.put(f'/visits/{sample_visit.id}',
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Status should remain unchanged
        assert data['visit']['status'] == original_status
        assert data['visit']['additional_notes'] == 'Updated notes'