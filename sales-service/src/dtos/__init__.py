"""
DTOs (Data Transfer Objects) para el servicio de visitas

Este módulo contiene los DTOs para transferencia de datos entre capas,
con validaciones usando Pydantic.
"""

from .create_visit_request import CreateVisitRequest
from .update_visit_request import UpdateVisitRequest  
from .visit_response import VisitResponse
from .basic_info_dtos import CustomerBasicInfo, SalespersonBasicInfo
from .visit_filters_and_utils import (
    VisitFilterRequest,
    VisitStatsResponse,
    FileUploadRequest,
    BulkVisitUpdateRequest
)
from .visit_file_dtos import (
    VisitFileResponse,
    VisitFileUploadRequest,
    VisitFileListResponse,
    FileUploadResponse,
    FileDeleteResponse
)

__all__ = [
    # Visit DTOs
    'CreateVisitRequest',
    'UpdateVisitRequest',
    'VisitResponse', 
    
    # Basic Info DTOs
    'CustomerBasicInfo',
    'SalespersonBasicInfo',
    
    # Filter and Utils DTOs
    'VisitFilterRequest',
    'VisitStatsResponse',
    'FileUploadRequest',
    'BulkVisitUpdateRequest',
    
    # File DTOs
    'VisitFileResponse',
    'VisitFileUploadRequest',
    'VisitFileListResponse',
    'FileUploadResponse',
    'FileDeleteResponse'
]