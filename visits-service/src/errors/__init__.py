"""
Manejo de errores para el servicio de visitas
"""

from .errors import (
    ApiError,
    NotFoundError,
    ValidationError,
    VisitValidationError,
    ForbiddenError,
    ConflictError,
    DatabaseError,
    ExternalServiceError,
    register_error_handlers
)

__all__ = [
    'ApiError',
    'NotFoundError',
    'ValidationError',
    'VisitValidationError',
    'ForbiddenError',
    'ConflictError',
    'DatabaseError',
    'ExternalServiceError',
    'register_error_handlers'
]