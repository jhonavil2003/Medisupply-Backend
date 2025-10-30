import pytest
from datetime import date, time
from src.entities.visit import Visit
from src.entities.salesperson import Salesperson
from src.entities.visit_status import VisitStatus


class TestVisit:
    """Tests para la entidad Visit"""
    
    def test_visit_creation(self, db_session):
        """Test crear una visita"""
        # Crear salesperson primero
        salesperson = Salesperson(
            employee_id="TEST-001",
            first_name="Juan",
            last_name="Pérez",
            email="juan.test@medisupply.com"
        )
        db_session.add(salesperson)
        db_session.commit()
        
        # Crear visita
        visit = Visit(
            customer_id=1,
            salesperson_id=salesperson.id,
            visit_date=date(2025, 11, 1),
            visit_time=time(10, 0),
            contacted_persons="Dr. Test",
            clinical_findings="Test findings",
            status=VisitStatus.SCHEDULED
        )
        
        db_session.add(visit)
        db_session.commit()
        
        assert visit.id is not None
        assert visit.customer_id == 1
        assert visit.salesperson_id == salesperson.id
        assert visit.status == VisitStatus.SCHEDULED
    
    def test_visit_to_dict(self, db_session):
        """Test serialización a diccionario"""
        salesperson = Salesperson(
            employee_id="TEST-002",
            first_name="María",
            last_name="González",
            email="maria.test@medisupply.com"
        )
        db_session.add(salesperson)
        db_session.commit()
        
        visit = Visit(
            customer_id=2,
            salesperson_id=salesperson.id,
            visit_date=date(2025, 11, 2),
            visit_time=time(14, 30)
        )
        
        db_session.add(visit)
        db_session.commit()
        
        result = visit.to_dict()
        
        assert result['customer_id'] == 2
        assert result['visit_date'] == "2025-11-02"
        assert result['visit_time'] == "14:30:00"
        assert 'id' in result