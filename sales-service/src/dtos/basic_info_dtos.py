from pydantic import BaseModel, Field
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List
from src.entities.visit_status import VisitStatus


class CustomerBasicInfo(BaseModel):
    """Información básica del cliente para respuestas"""
    
    id: int = Field(..., description="ID del cliente")
    business_name: str = Field(..., description="Razón social")
    contact_name: Optional[str] = Field(None, description="Nombre del contacto")
    contact_email: Optional[str] = Field(None, description="Email del contacto")
    contact_phone: Optional[str] = Field(None, description="Teléfono del contacto")
    document_number: Optional[str] = Field(None, description="Número de documento")
    city: Optional[str] = Field(None, description="Ciudad")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "business_name": "Hospital Universitario San Ignacio",
                "contact_name": "Dr. María González",
                "contact_email": "maria.gonzalez@husi.org.co",
                "contact_phone": "+57 1 594 6161",
                "document_number": "900123456-1",
                "city": "Bogotá"
            }
        }


class SalespersonBasicInfo(BaseModel):
    """Información básica del vendedor para respuestas"""
    
    id: int = Field(..., description="ID del vendedor")
    employee_id: str = Field(..., description="ID del empleado")
    first_name: str = Field(..., description="Nombre")
    last_name: str = Field(..., description="Apellido")
    full_name: str = Field(..., description="Nombre completo")
    email: str = Field(..., description="Email")
    territory: Optional[str] = Field(None, description="Territorio")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "employee_id": "SELLER-001",
                "first_name": "Juan",
                "last_name": "Pérez",
                "full_name": "Juan Pérez",
                "email": "juan.perez@medisupply.com",
                "territory": "Bogotá Norte"
            }
        }


class VisitFileResponse(BaseModel):
    """Respuesta para archivos adjuntos de visita"""
    
    id: int = Field(..., description="ID del archivo")
    file_name: str = Field(..., description="Nombre del archivo")
    file_path: str = Field(..., description="Ruta del archivo")
    file_size: Optional[int] = Field(None, description="Tamaño en bytes")
    file_size_formatted: Optional[str] = Field(None, description="Tamaño formateado")
    mime_type: Optional[str] = Field(None, description="Tipo MIME")
    uploaded_at: datetime = Field(..., description="Fecha de carga")
    is_image: bool = Field(False, description="Es una imagen")
    is_document: bool = Field(False, description="Es un documento")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": 1,
                "file_name": "inventory_report.pdf",
                "file_path": "/uploads/visits/1/inventory_report.pdf",
                "file_size": 1024000,
                "file_size_formatted": "1.0 MB",
                "mime_type": "application/pdf",
                "uploaded_at": "2025-10-28T14:30:00",
                "is_image": False,
                "is_document": True
            }
        }