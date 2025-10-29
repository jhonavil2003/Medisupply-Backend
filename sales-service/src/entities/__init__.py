"""
Entities package - Contiene las entidades del dominio para el módulo de visitas
Siguiendo el patrón JPA/Hibernate de Java
"""

from .visit_status import VisitStatus
from .salesperson import Salesperson
from .visit import Visit
from .visit_file import VisitFile

__all__ = ['VisitStatus', 'Salesperson', 'Visit', 'VisitFile']