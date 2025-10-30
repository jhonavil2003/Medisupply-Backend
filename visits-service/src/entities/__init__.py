"""
Entidades del servicio de visitas

Este módulo contiene las entidades de dominio para el servicio de visitas,
siguiendo el patrón de diseño de entidades JPA con getters/setters.
"""

from .salesperson import Salesperson
from .visit_status import VisitStatus
from .visit import Visit
from .visit_file import VisitFile

__all__ = [
    'Salesperson',
    'VisitStatus', 
    'Visit',
    'VisitFile'
]