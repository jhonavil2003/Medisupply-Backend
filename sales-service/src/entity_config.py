"""
Entity Configuration - Configura las entidades para su uso en la aplicación
"""

# Import all entities to ensure they are registered with SQLAlchemy
from src.entities.visit_status import VisitStatus
from src.entities.salesperson import Salesperson  
from src.entities.visit import Visit
from src.entities.visit_file import VisitFile

# Import existing models to maintain compatibility
from src.models.customer import Customer
from src.models.order import Order
from src.models.order_item import OrderItem
from src.models.commercial_condition import CommercialCondition

# Export all for easy importing
__all__ = [
    # New entities
    'VisitStatus',
    'Salesperson',
    'Visit', 
    'VisitFile',
    # Existing models
    'Customer',
    'Order',
    'OrderItem',
    'CommercialCondition'
]