import pytest
from src.entities.salesperson import Salesperson


class TestSalesperson:
    """Tests para la entidad Salesperson"""
    
    def test_salesperson_creation(self, db_session):
        """Test crear un salesperson"""
        salesperson = Salesperson(
            employee_id="TEST-001",
            first_name="Juan",
            last_name="Pérez",
            email="juan.test@medisupply.com",
            phone="+57 300 1234567",
            territory="Bogotá",
            is_active=True
        )
        
        db_session.add(salesperson)
        db_session.commit()
        
        assert salesperson.id is not None
        assert salesperson.employee_id == "TEST-001"
        assert salesperson.get_full_name() == "Juan Pérez"
        assert salesperson.is_active is True
    
    def test_salesperson_to_dict(self, db_session):
        """Test serialización a diccionario"""
        salesperson = Salesperson(
            employee_id="TEST-002",
            first_name="María",
            last_name="González",
            email="maria.test@medisupply.com"
        )
        
        db_session.add(salesperson)
        db_session.commit()
        
        result = salesperson.to_dict()
        
        assert result['employee_id'] == "TEST-002"
        assert result['full_name'] == "María González"
        assert 'id' in result
        assert 'created_at' in result