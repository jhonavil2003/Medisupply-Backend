"""
DTOs package - Contiene los Data Transfer Objects para el módulo de visitas
Siguiendo el patrón DTO de Java para validación y serialización
"""

# Request DTOs
from .create_visit_request import CreateVisitRequest
from .update_visit_request import UpdateVisitRequest

# Response DTOs
from .basic_info_dtos import CustomerBasicInfo, SalespersonBasicInfo, VisitFileResponse
from .visit_response import VisitResponse, VisitListResponse, VisitListResult

# Filter and Utility DTOs
from .visit_filters_and_utils import (
    VisitFilterRequest, 
    VisitStatsResponse, 
    FileUploadRequest,
    BulkVisitUpdateRequest
)

__all__ = [
    # Request DTOs
    'CreateVisitRequest',
    'UpdateVisitRequest',
    
    # Response DTOs
    'CustomerBasicInfo',
    'SalespersonBasicInfo', 
    'VisitFileResponse',
    'VisitResponse',
    'VisitListResponse',
    'VisitListResult',
    
    # Filter and Utility DTOs
    'VisitFilterRequest',
    'VisitStatsResponse',
    'FileUploadRequest',
    'BulkVisitUpdateRequest'
]