from src.entities.salesperson_goal import SalespersonGoal
from src.errors.errors import NotFoundError


class GetSalespersonGoalById:
    """Command to retrieve a salesperson goal by ID."""
    
    def __init__(self, goal_id):
        self.goal_id = goal_id
    
    def execute(self):
        """
        Execute the command to get a goal by ID.
        
        Returns:
            dict: Goal data
            
        Raises:
            NotFoundError: If goal not found
        """
        goal = SalespersonGoal.query.get(self.goal_id)
        
        if not goal:
            raise NotFoundError(f"Objetivo con ID {self.goal_id} no encontrado")
        
        return goal.to_dict(include_salesperson=True, include_producto=True)