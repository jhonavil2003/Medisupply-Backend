from src.entities.salesperson_goal import SalespersonGoal
from src.session import db
from src.errors.errors import NotFoundError


class DeleteSalespersonGoal:
    """Command to delete a salesperson goal."""
    
    def __init__(self, goal_id):
        self.goal_id = goal_id
    
    def execute(self):
        """
        Execute the command to delete a goal.
        
        Returns:
            dict: Deleted goal data
            
        Raises:
            NotFoundError: If goal not found
        """
        goal = SalespersonGoal.query.get(self.goal_id)
        
        if not goal:
            raise NotFoundError(f"Objetivo con ID {self.goal_id} no encontrado")
        
        # Save goal data before deletion
        goal_data = goal.to_dict(include_salesperson=True, include_producto=True)
        
        # Delete goal
        db.session.delete(goal)
        db.session.commit()
        
        return {
            'message': f'Objetivo con ID {self.goal_id} eliminado exitosamente',
            'deleted_goal': goal_data
        }
