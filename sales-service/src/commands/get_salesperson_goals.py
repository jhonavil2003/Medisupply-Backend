from src.entities.salesperson_goal import SalespersonGoal
from src.session import db


class GetSalespersonGoals:
    """Command to retrieve salesperson goals with optional filters."""
    
    def __init__(self, filters=None):
        self.filters = filters or {}
    
    def execute(self):
        """
        Execute the command to get goals.
        
        Returns:
            list: List of goal dictionaries
        """
        query = SalespersonGoal.query
        
        # Apply filters
        if 'id_vendedor' in self.filters and self.filters['id_vendedor']:
            query = query.filter(SalespersonGoal.id_vendedor == self.filters['id_vendedor'])
        
        if 'id_producto' in self.filters and self.filters['id_producto']:
            query = query.filter(SalespersonGoal.id_producto == self.filters['id_producto'])
        
        if 'region' in self.filters and self.filters['region']:
            query = query.filter(SalespersonGoal.region == self.filters['region'])
        
        if 'trimestre' in self.filters and self.filters['trimestre']:
            query = query.filter(SalespersonGoal.trimestre == self.filters['trimestre'])
        
        if 'tipo' in self.filters and self.filters['tipo']:
            query = query.filter(SalespersonGoal.tipo == self.filters['tipo'])
        
        # Order by fecha_creacion descending
        goals = query.order_by(SalespersonGoal.fecha_creacion.desc()).all()
        
        return [goal.to_dict(include_salesperson=True, include_producto=True) for goal in goals]
