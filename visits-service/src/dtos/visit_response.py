from pydantic import BaseModel, Field
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from src.entities.visit_status import VisitStatus
from .basic_info_dtos import CustomerBasicInfo, SalespersonBasicInfo

if TYPE_CHECKING:
    from .visit_file_dtos import VisitFileResponse


class VisitResponse(BaseModel):
    """Respuesta completa para una visita"""
    
    id: int = Field(..., description="ID de la visita")
    customer: CustomerBasicInfo = Field(..., description="Información del cliente")
    salesperson: SalespersonBasicInfo = Field(..., description="Información del vendedor")
    
    # Información de la visita
    visit_date: date = Field(..., description="Fecha de visita")
    visit_time: time = Field(..., description="Hora de visita")
    contacted_persons: Optional[str] = Field(None, description="Personas contactadas")
    clinical_findings: Optional[str] = Field(None, description="Hallazgos clínicos")
    additional_notes: Optional[str] = Field(None, description="Notas adicionales")
    
    # Ubicación
    address: Optional[str] = Field(None, description="Dirección")
    latitude: Optional[Decimal] = Field(None, description="Latitud")
    longitude: Optional[Decimal] = Field(None, description="Longitud")
    
    # Estado y archivos
    status: VisitStatus = Field(..., description="Estado de la visita")
    files: List['VisitFileResponse'] = Field(default_factory=list, description="Archivos adjuntos")
    files_count: int = Field(0, description="Número de archivos")
    
    # Timestamps
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            time: lambda v: v.strftime("%H:%M:%S"),
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v) if v else None,
            VisitStatus: lambda v: v.value
        }
        schema_extra = {
            "example": {
                "id": 1,
                "customer": {
                    "id": 1,
                    "business_name": "Hospital Universitario San Ignacio",
                    "contact_name": "Dr. María González",
                    "contact_email": "maria.gonzalez@husi.org.co",
                    "contact_phone": "+57 1 594 6161",
                    "document_number": "900123456-1",
                    "city": "Bogotá"
                },
                "salesperson": {
                    "id": 1,
                    "employee_id": "SELLER-001",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "full_name": "Juan Pérez",
                    "email": "juan.perez@medisupply.com",
                    "territory": "Bogotá Norte"
                },
                "visit_date": "2025-10-30",
                "visit_time": "14:30:00",
                "contacted_persons": "Dr. María González, Ana López - Enfermera Jefe",
                "clinical_findings": "Inventario bajo en jeringas desechables y gasas estériles",
                "additional_notes": "Cliente interesado en productos ortopédicos nuevos",
                "address": "Calle 10 #5-25, Bogotá",
                "latitude": 4.60971,
                "longitude": -74.08175,
                "status": "COMPLETED",
                "files": [],
                "files_count": 0,
                "created_at": "2025-10-28T14:30:00",
                "updated_at": "2025-10-28T16:45:00"
            }
        }


class VisitListResponse(BaseModel):
    """Respuesta para lista de visitas (información resumida)"""
    
    id: int = Field(..., description="ID de la visita")
    customer_id: int = Field(..., description="ID del cliente")
    customer_name: str = Field(..., description="Nombre del cliente")
    salesperson_id: int = Field(..., description="ID del vendedor")
    salesperson_name: str = Field(..., description="Nombre del vendedor")
    
    visit_date: date = Field(..., description="Fecha de visita")
    visit_time: time = Field(..., description="Hora de visita")
    address: Optional[str] = Field(None, description="Dirección")
    status: VisitStatus = Field(..., description="Estado de la visita")
    files_count: int = Field(0, description="Número de archivos")
    
    created_at: datetime = Field(..., description="Fecha de creación")
    
    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            time: lambda v: v.strftime("%H:%M:%S"),
            datetime: lambda v: v.isoformat(),
            VisitStatus: lambda v: v.value
        }
        schema_extra = {
            "example": {
                "id": 1,
                "customer_id": 1,
                "customer_name": "Hospital Universitario San Ignacio",
                "salesperson_id": 1,
                "salesperson_name": "Juan Pérez",
                "visit_date": "2025-10-30",
                "visit_time": "14:30:00",
                "address": "Calle 10 #5-25, Bogotá",
                "status": "SCHEDULED",
                "files_count": 2,
                "created_at": "2025-10-28T14:30:00"
            }
        }


class VisitListResult(BaseModel):
    """Resultado paginado para lista de visitas"""
    
    visits: List[VisitListResponse] = Field(default_factory=list, description="Lista de visitas")
    total: int = Field(0, description="Total de visitas")
    page: int = Field(1, description="Página actual")
    per_page: int = Field(20, description="Elementos por página")
    pages: int = Field(0, description="Total de páginas")
    
    class Config:
        schema_extra = {
            "example": {
                "visits": [
                    {
                        "id": 1,
                        "customer_id": 1,
                        "customer_name": "Hospital Universitario San Ignacio",
                        "salesperson_id": 1,
                        "salesperson_name": "Juan Pérez",
                        "visit_date": "2025-10-30",
                        "visit_time": "14:30:00",
                        "address": "Calle 10 #5-25, Bogotá",
                        "status": "SCHEDULED",
                        "files_count": 0,
                        "created_at": "2025-10-28T14:30:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 20,
                "pages": 1
            }
        }