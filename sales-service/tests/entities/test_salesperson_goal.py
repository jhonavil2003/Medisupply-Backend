import pytest
from decimal import Decimal
from src.entities.salesperson_goal import SalespersonGoal, GoalType, Region, Quarter


class TestSalespersonGoalEntity:
    """Test cases for SalespersonGoal entity"""
    
    def test_create_goal_instance(self):
        """Test creating a SalespersonGoal instance."""
        goal = SalespersonGoal(
            id_vendedor='EMP001',
            id_producto='JER-001',
            region=Region.NORTE.value,
            trimestre=Quarter.Q1.value,
            valor_objetivo=50000.00,
            tipo=GoalType.MONETARIO.value
        )
        
        assert goal.id_vendedor == 'EMP001'
        assert goal.id_producto == 'JER-001'
        assert goal.region == Region.NORTE.value
        assert goal.trimestre == Quarter.Q1.value
        assert goal.valor_objetivo == 50000.00
        assert goal.tipo == GoalType.MONETARIO.value
    
    def test_goal_repr(self, sample_salesperson_goal):
        """Test string representation of goal."""
        repr_str = repr(sample_salesperson_goal)
        
        assert 'SalespersonGoal' in repr_str
        assert str(sample_salesperson_goal.id) in repr_str
        assert sample_salesperson_goal.id_vendedor in repr_str
        assert sample_salesperson_goal.id_producto in repr_str
    
    def test_goal_getters(self, sample_salesperson_goal):
        """Test getter methods."""
        assert sample_salesperson_goal.get_id() == sample_salesperson_goal.id
        assert sample_salesperson_goal.get_id_vendedor() == sample_salesperson_goal.id_vendedor
        assert sample_salesperson_goal.get_id_producto() == sample_salesperson_goal.id_producto
        assert sample_salesperson_goal.get_region() == sample_salesperson_goal.region
        assert sample_salesperson_goal.get_trimestre() == sample_salesperson_goal.trimestre
        assert sample_salesperson_goal.get_valor_objetivo() == float(sample_salesperson_goal.valor_objetivo)
        assert sample_salesperson_goal.get_tipo() == sample_salesperson_goal.tipo
    
    def test_goal_setters(self, sample_salesperson_goal):
        """Test setter methods."""
        sample_salesperson_goal.set_id(999)
        assert sample_salesperson_goal.id == 999
        
        sample_salesperson_goal.set_id_vendedor('EMP002')
        assert sample_salesperson_goal.id_vendedor == 'EMP002'
        
        sample_salesperson_goal.set_id_producto('VAC-001')
        assert sample_salesperson_goal.id_producto == 'VAC-001'
        
        sample_salesperson_goal.set_region(Region.SUR.value)
        assert sample_salesperson_goal.region == Region.SUR.value
        
        sample_salesperson_goal.set_trimestre(Quarter.Q2.value)
        assert sample_salesperson_goal.trimestre == Quarter.Q2.value
        
        sample_salesperson_goal.set_valor_objetivo(75000.00)
        assert sample_salesperson_goal.valor_objetivo == 75000.00
        
        sample_salesperson_goal.set_tipo(GoalType.UNIDADES.value)
        assert sample_salesperson_goal.tipo == GoalType.UNIDADES.value
    
    def test_is_monetary_goal(self, sample_salesperson_goal):
        """Test is_monetary_goal method."""
        sample_salesperson_goal.tipo = GoalType.MONETARIO.value
        assert sample_salesperson_goal.is_monetary_goal() is True
        
        sample_salesperson_goal.tipo = GoalType.UNIDADES.value
        assert sample_salesperson_goal.is_monetary_goal() is False
    
    def test_is_units_goal(self, sample_salesperson_goal):
        """Test is_units_goal method."""
        sample_salesperson_goal.tipo = GoalType.UNIDADES.value
        assert sample_salesperson_goal.is_units_goal() is True
        
        sample_salesperson_goal.tipo = GoalType.MONETARIO.value
        assert sample_salesperson_goal.is_units_goal() is False
    
    def test_get_goal_description_monetary(self, sample_salesperson_goal):
        """Test get_goal_description for monetary goal."""
        sample_salesperson_goal.tipo = GoalType.MONETARIO.value
        sample_salesperson_goal.valor_objetivo = Decimal('50000.00')
        sample_salesperson_goal.trimestre = Quarter.Q1.value
        sample_salesperson_goal.region = Region.NORTE.value
        
        description = sample_salesperson_goal.get_goal_description()
        
        assert 'monetario' in description
        assert '50000' in description
        assert 'Q1' in description
        assert 'Norte' in description
    
    def test_get_goal_description_units(self, sample_salesperson_goal):
        """Test get_goal_description for units goal."""
        sample_salesperson_goal.tipo = GoalType.UNIDADES.value
        sample_salesperson_goal.valor_objetivo = Decimal('100')
        sample_salesperson_goal.trimestre = Quarter.Q2.value
        sample_salesperson_goal.region = Region.SUR.value
        
        description = sample_salesperson_goal.get_goal_description()
        
        assert 'unidades' in description
        assert '100' in description
        assert 'Q2' in description
        assert 'Sur' in description
    
    def test_to_dict_basic(self, sample_salesperson_goal):
        """Test to_dict without includes."""
        goal_dict = sample_salesperson_goal.to_dict()
        
        assert 'id' in goal_dict
        assert 'id_vendedor' in goal_dict
        assert 'id_producto' in goal_dict
        assert 'region' in goal_dict
        assert 'trimestre' in goal_dict
        assert 'valor_objetivo' in goal_dict
        assert 'tipo' in goal_dict
        assert 'fecha_creacion' in goal_dict
        assert 'fecha_actualizacion' in goal_dict
        assert 'vendedor' not in goal_dict
        assert 'producto' not in goal_dict
    
    def test_to_dict_with_salesperson(self, sample_salesperson_goal):
        """Test to_dict with include_salesperson."""
        goal_dict = sample_salesperson_goal.to_dict(include_salesperson=True)
        
        assert 'vendedor' in goal_dict
        assert goal_dict['vendedor']['employee_id'] == sample_salesperson_goal.id_vendedor
        assert 'nombre_completo' in goal_dict['vendedor']
        assert 'email' in goal_dict['vendedor']
    
    def test_to_dict_with_producto_exception(self, sample_salesperson_goal, monkeypatch):
        """Test to_dict with include_producto when IntegrationService fails."""
        # Mock IntegrationService.get_product_by_sku to raise an exception
        def mock_get_product_error(sku):
            raise Exception("Service unavailable")
        
        from src.services import integration_service
        monkeypatch.setattr(integration_service.IntegrationService, 'get_product_by_sku', mock_get_product_error)
        
        goal_dict = sample_salesperson_goal.to_dict(include_producto=True)
        
        assert 'producto' in goal_dict
        assert goal_dict['producto']['sku'] == sample_salesperson_goal.id_producto
        assert goal_dict['producto']['name'] is None
        assert goal_dict['producto']['description'] is None
    
    def test_validate_region_valid(self):
        """Test validate_region with valid regions."""
        assert SalespersonGoal.validate_region(Region.NORTE.value) is True
        assert SalespersonGoal.validate_region(Region.SUR.value) is True
        assert SalespersonGoal.validate_region(Region.ESTE.value) is True
        assert SalespersonGoal.validate_region(Region.OESTE.value) is True
    
    def test_validate_region_invalid(self):
        """Test validate_region with invalid region."""
        assert SalespersonGoal.validate_region('InvalidRegion') is False
        assert SalespersonGoal.validate_region('Centro') is False
        assert SalespersonGoal.validate_region('') is False
    
    def test_validate_quarter_valid(self):
        """Test validate_quarter with valid quarters."""
        assert SalespersonGoal.validate_quarter(Quarter.Q1.value) is True
        assert SalespersonGoal.validate_quarter(Quarter.Q2.value) is True
        assert SalespersonGoal.validate_quarter(Quarter.Q3.value) is True
        assert SalespersonGoal.validate_quarter(Quarter.Q4.value) is True
    
    def test_validate_quarter_invalid(self):
        """Test validate_quarter with invalid quarter."""
        assert SalespersonGoal.validate_quarter('Q5') is False
        assert SalespersonGoal.validate_quarter('Quarter1') is False
        assert SalespersonGoal.validate_quarter('') is False
    
    def test_validate_goal_type_valid(self):
        """Test validate_goal_type with valid types."""
        assert SalespersonGoal.validate_goal_type(GoalType.MONETARIO.value) is True
        assert SalespersonGoal.validate_goal_type(GoalType.UNIDADES.value) is True
    
    def test_validate_goal_type_invalid(self):
        """Test validate_goal_type with invalid type."""
        assert SalespersonGoal.validate_goal_type('invalid_type') is False
        assert SalespersonGoal.validate_goal_type('percentage') is False
        assert SalespersonGoal.validate_goal_type('') is False
    
    def test_goal_persistence(self, db, sample_salesperson):
        """Test saving and retrieving goal from database."""
        goal = SalespersonGoal(
            id_vendedor=sample_salesperson.employee_id,
            id_producto='TEST-PERSIST',
            region=Region.OESTE.value,
            trimestre=Quarter.Q3.value,
            valor_objetivo=25000.00,
            tipo=GoalType.UNIDADES.value
        )
        
        db.session.add(goal)
        db.session.commit()
        
        # Retrieve from database
        retrieved_goal = db.session.get(SalespersonGoal, goal.id)
        
        assert retrieved_goal is not None
        assert retrieved_goal.id_vendedor == sample_salesperson.employee_id
        assert retrieved_goal.id_producto == 'TEST-PERSIST'
        assert retrieved_goal.region == Region.OESTE.value
        assert retrieved_goal.trimestre == Quarter.Q3.value
        assert float(retrieved_goal.valor_objetivo) == 25000.00
        assert retrieved_goal.tipo == GoalType.UNIDADES.value
    
    def test_goal_relationship_with_salesperson(self, db, sample_salesperson):
        """Test relationship between goal and salesperson."""
        goal = SalespersonGoal(
            id_vendedor=sample_salesperson.employee_id,
            id_producto='TEST-REL',
            region=Region.NORTE.value,
            trimestre=Quarter.Q1.value,
            valor_objetivo=50000.00,
            tipo=GoalType.MONETARIO.value
        )
        
        db.session.add(goal)
        db.session.commit()
        
        # Access relationship
        assert goal.salesperson is not None
        assert goal.salesperson.employee_id == sample_salesperson.employee_id
        assert goal.salesperson.first_name == sample_salesperson.first_name
    
    def test_goal_timestamps(self, db, sample_salesperson):
        """Test that timestamps are set automatically."""
        goal = SalespersonGoal(
            id_vendedor=sample_salesperson.employee_id,
            id_producto='TEST-TIME',
            region=Region.NORTE.value,
            trimestre=Quarter.Q1.value,
            valor_objetivo=50000.00,
            tipo=GoalType.MONETARIO.value
        )
        
        db.session.add(goal)
        db.session.commit()
        
        assert goal.fecha_creacion is not None
        assert goal.fecha_actualizacion is not None
        assert goal.get_fecha_creacion() is not None
        assert goal.get_fecha_actualizacion() is not None


class TestGoalTypeEnum:
    """Test cases for GoalType enum"""
    
    def test_goal_type_values(self):
        """Test GoalType enum values."""
        assert GoalType.UNIDADES.value == 'unidades'
        assert GoalType.MONETARIO.value == 'monetario'
    
    def test_goal_type_count(self):
        """Test that GoalType has exactly 2 values."""
        assert len(list(GoalType)) == 2


class TestRegionEnum:
    """Test cases for Region enum"""
    
    def test_region_values(self):
        """Test Region enum values."""
        assert Region.NORTE.value == 'Norte'
        assert Region.SUR.value == 'Sur'
        assert Region.OESTE.value == 'Oeste'
        assert Region.ESTE.value == 'Este'
    
    def test_region_count(self):
        """Test that Region has exactly 4 values."""
        assert len(list(Region)) == 4


class TestQuarterEnum:
    """Test cases for Quarter enum"""
    
    def test_quarter_values(self):
        """Test Quarter enum values."""
        assert Quarter.Q1.value == 'Q1'
        assert Quarter.Q2.value == 'Q2'
        assert Quarter.Q3.value == 'Q3'
        assert Quarter.Q4.value == 'Q4'
    
    def test_quarter_count(self):
        """Test that Quarter has exactly 4 values."""
        assert len(list(Quarter)) == 4
