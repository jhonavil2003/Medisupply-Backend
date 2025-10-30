"""
DTOs (Data Transfer Objects) para el servicio de visitas

Este módulo contiene los DTOs para transferencia de datos entre capas,
con validaciones usando Pydantic.
"""

from .create_visit_request import CreateVisitRequest
from .update_visit_request import UpdateVisitRequest  
from .visit_response import VisitResponse
from .visit_filters_and_utils import (
    VisitFilterRequest,
    VisitSortBy,
    SortOrder,
    VisitStatsResponse,
    VisitListResponse,
    UpdateVisitStatusRequest,
    VisitFileRequest,
    VisitFileResponse,
    SalespersonResponse
)

__all__ = [
    'CreateVisitRequest',
    'UpdateVisitRequest',
    'VisitResponse', 
    'VisitFilterRequest',
    'VisitSortBy',
    'SortOrder',
    'VisitStatsResponse',
    'VisitListResponse',
    'UpdateVisitStatusRequest',
    'VisitFileRequest',
    'VisitFileResponse',
    'SalespersonResponse'
]