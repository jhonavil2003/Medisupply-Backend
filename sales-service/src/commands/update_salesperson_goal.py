from src.entities.salesperson_goal import SalespersonGoal, GoalType, Region, Quarter
from src.session import db
from src.errors.errors import ValidationError, NotFoundError
from datetime import datetime


class UpdateSalespersonGoal:
    """Command to update an existing salesperson goal."""
    
    def __init__(self, goal_id, data):
        self.goal_id = goal_id
        self.data = data
    
    def execute(self):
        """
        Execute the command to update a goal.
        
        Returns:
            dict: Updated goal data
            
        Raises:
            ValidationError: If validation fails or goal not found
        """
        # Get existing goal
        goal = self._get_goal()
        
        # Validate business rules for updated fields
        self._validate_business_rules()
        
        # Check for duplicate if key fields are being updated
        if self._key_fields_changed(goal):
            self._check_duplicate_goal(goal)
        
        # Update goal
        updated_goal = self._update_goal(goal)
        
        return updated_goal.to_dict(include_salesperson=True, include_producto=True)
    
    def _get_goal(self):
        """Get the goal to update."""
        goal = SalespersonGoal.query.get(self.goal_id)
        
        if not goal:
            raise NotFoundError(f"Objetivo con ID {self.goal_id} no encontrado")
        
        return goal
    
    def _validate_business_rules(self):
        """Validate business rules for fields being updated."""
        # Validate region if provided
        if 'region' in self.data and self.data['region'] is not None:
            if not SalespersonGoal.validate_region(self.data['region']):
                valid_regions = [r.value for r in Region]
                raise ValidationError(f"La región debe ser una de: {', '.join(valid_regions)}")
        
        # Validate quarter if provided
        if 'trimestre' in self.data and self.data['trimestre'] is not None:
            if not SalespersonGoal.validate_quarter(self.data['trimestre']):
                valid_quarters = [q.value for q in Quarter]
                raise ValidationError(f"El trimestre debe ser uno de: {', '.join(valid_quarters)}")
        
        # Validate goal type if provided
        if 'tipo' in self.data and self.data['tipo'] is not None:
            if not SalespersonGoal.validate_goal_type(self.data['tipo']):
                valid_types = [t.value for t in GoalType]
                raise ValidationError(f"El tipo debe ser uno de: {', '.join(valid_types)}")
        
        # Validate valor_objetivo if provided
        if 'valor_objetivo' in self.data and self.data['valor_objetivo'] is not None:
            try:
                valor = float(self.data['valor_objetivo'])
                if valor <= 0:
                    raise ValidationError("El valor_objetivo debe ser mayor a 0")
            except (ValueError, TypeError):
                raise ValidationError("El valor_objetivo debe ser un número válido")
    
    def _key_fields_changed(self, goal):
        """Check if any key fields that define uniqueness are being changed."""
        key_fields = ['id_vendedor', 'id_producto', 'region', 'trimestre']
        
        for field in key_fields:
            if field in self.data and self.data[field] is not None:
                if getattr(goal, field) != self.data[field]:
                    return True
        
        return False
    
    def _check_duplicate_goal(self, current_goal):
        """Check if updated goal would create a duplicate."""
        # Build filter with new values or existing values
        filters = {
            'id_vendedor': self.data.get('id_vendedor', current_goal.id_vendedor),
            'id_producto': self.data.get('id_producto', current_goal.id_producto),
            'region': self.data.get('region', current_goal.region),
            'trimestre': self.data.get('trimestre', current_goal.trimestre)
        }
        
        existing_goal = SalespersonGoal.query.filter_by(**filters).first()
        
        if existing_goal and existing_goal.id != self.goal_id:
            raise ValidationError(
                f"Ya existe un objetivo para el vendedor '{filters['id_vendedor']}', "
                f"producto '{filters['id_producto']}', región '{filters['region']}' "
                f"y trimestre '{filters['trimestre']}'"
            )
    
    def _update_goal(self, goal):
        """Update the goal with new data."""
        # Update fields if provided
        if 'id_vendedor' in self.data and self.data['id_vendedor'] is not None:
            goal.id_vendedor = self.data['id_vendedor']
        
        if 'id_producto' in self.data and self.data['id_producto'] is not None:
            goal.id_producto = self.data['id_producto']
        
        if 'region' in self.data and self.data['region'] is not None:
            goal.region = self.data['region']
        
        if 'trimestre' in self.data and self.data['trimestre'] is not None:
            goal.trimestre = self.data['trimestre']
        
        if 'valor_objetivo' in self.data and self.data['valor_objetivo'] is not None:
            goal.valor_objetivo = float(self.data['valor_objetivo'])
        
        if 'tipo' in self.data and self.data['tipo'] is not None:
            goal.tipo = self.data['tipo']
        
        # Update timestamp
        goal.fecha_actualizacion = datetime.utcnow()
        
        db.session.commit()
        db.session.refresh(goal)
        
        return goal
