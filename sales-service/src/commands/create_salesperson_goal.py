from src.entities.salesperson_goal import SalespersonGoal, GoalType, Region, Quarter
from src.entities.salesperson import Salesperson
from src.session import db
from src.errors.errors import ValidationError


class CreateSalespersonGoal:
    """Command to create a new salesperson goal with validation."""
    
    def __init__(self, data):
        self.data = data
    
    def execute(self):
        """
        Execute the command to create a salesperson goal.
        
        Returns:
            dict: Created goal data
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate required fields
        self._validate_required_fields()
        
        # Validate business rules
        self._validate_business_rules()
        
        # Check if salesperson exists
        self._check_salesperson_exists()
        
        # Check for duplicate goal
        self._check_duplicate_goal()
        
        # Create goal
        goal = self._create_goal()
        
        return goal.to_dict(include_salesperson=True, include_producto=True)
    
    def _validate_required_fields(self):
        """Validate required fields are present."""
        required_fields = [
            'id_vendedor',
            'id_producto',
            'region',
            'trimestre',
            'valor_objetivo',
            'tipo'
        ]
        
        for field in required_fields:
            if field not in self.data or self.data[field] is None:
                raise ValidationError(f"Campo requerido: '{field}'")
    
    def _validate_business_rules(self):
        """Validate business rules and data formats."""
        # Validate region
        if not SalespersonGoal.validate_region(self.data['region']):
            valid_regions = [r.value for r in Region]
            raise ValidationError(f"La región debe ser una de: {', '.join(valid_regions)}")
        
        # Validate quarter
        if not SalespersonGoal.validate_quarter(self.data['trimestre']):
            valid_quarters = [q.value for q in Quarter]
            raise ValidationError(f"El trimestre debe ser uno de: {', '.join(valid_quarters)}")
        
        # Validate goal type
        if not SalespersonGoal.validate_goal_type(self.data['tipo']):
            valid_types = [t.value for t in GoalType]
            raise ValidationError(f"El tipo debe ser uno de: {', '.join(valid_types)}")
        
        # Validate valor_objetivo is positive
        try:
            valor = float(self.data['valor_objetivo'])
            if valor <= 0:
                raise ValidationError("El valor_objetivo debe ser mayor a 0")
        except (ValueError, TypeError):
            raise ValidationError("El valor_objetivo debe ser un número válido")
    
    def _check_salesperson_exists(self):
        """Check if salesperson exists."""
        salesperson = Salesperson.query.filter_by(
            employee_id=self.data['id_vendedor']
        ).first()
        
        if not salesperson:
            raise ValidationError(f"Vendedor con ID '{self.data['id_vendedor']}' no encontrado")
        
        if not salesperson.is_active:
            raise ValidationError(f"Vendedor con ID '{self.data['id_vendedor']}' no está activo")
    
    def _check_duplicate_goal(self):
        """Check if goal already exists for this combination."""
        existing_goal = SalespersonGoal.query.filter_by(
            id_vendedor=self.data['id_vendedor'],
            id_producto=self.data['id_producto'],
            region=self.data['region'],
            trimestre=self.data['trimestre']
        ).first()
        
        if existing_goal:
            raise ValidationError(
                f"Ya existe un objetivo para el vendedor '{self.data['id_vendedor']}', "
                f"producto '{self.data['id_producto']}', región '{self.data['region']}' "
                f"y trimestre '{self.data['trimestre']}'"
            )
    
    def _create_goal(self):
        """Create the goal in the database."""
        goal = SalespersonGoal(
            id_vendedor=self.data['id_vendedor'],
            id_producto=self.data['id_producto'],
            region=self.data['region'],
            trimestre=self.data['trimestre'],
            valor_objetivo=float(self.data['valor_objetivo']),
            tipo=self.data['tipo']
        )
        
        db.session.add(goal)
        db.session.commit()
        db.session.refresh(goal)
        
        return goal
