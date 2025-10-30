import pytest
import json
from datetime import date, time


class TestVisitsBlueprint:
    """Tests para el blueprint de visits"""
    
    def test_health_endpoint(self, client):
        """Test endpoint de health check"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['service'] == 'visits-service'
        assert data['status'] == 'healthy'
    
    def test_get_salespersons(self, client, db_session):
        """Test obtener salespersons"""
        from src.entities.salesperson import Salesperson
        
        # Crear salesperson de prueba
        salesperson = Salesperson(
            employee_id="TEST-001",
            first_name="Juan",
            last_name="Pérez",
            email="juan.test@medisupply.com",
            is_active=True
        )
        db_session.add(salesperson)
        db_session.commit()
        
        response = client.get('/api/visits/salespersons')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'salespersons' in data
        assert len(data['salespersons']) > 0
    
    def test_create_visit(self, client, db_session):
        """Test crear una visita"""
        from src.entities.salesperson import Salesperson
        
        # Crear salesperson de prueba
        salesperson = Salesperson(
            employee_id="TEST-002",
            first_name="María",
            last_name="González",
            email="maria.test@medisupply.com"
        )
        db_session.add(salesperson)
        db_session.commit()
        
        visit_data = {
            "customer_id": 1,
            "salesperson_id": salesperson.id,
            "visit_date": "2025-11-01",
            "visit_time": "10:00:00",
            "contacted_persons": "Dr. Test",
            "clinical_findings": "Test findings"
        }
        
        response = client.post('/api/visits',
                             data=json.dumps(visit_data),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['message'] == 'Visita creada exitosamente'
        assert 'visit' in data
    
    def test_get_visits(self, client):
        """Test obtener lista de visitas"""
        response = client.get('/api/visits')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'visits' in data