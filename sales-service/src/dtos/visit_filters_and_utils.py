from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional, List
from src.entities.visit_status import VisitStatus


class VisitFilterRequest(BaseModel):
    """DTO para filtrar visitas - equivalente a query parameters"""
    
    # Filtros principales
    customer_id: Optional[int] = Field(None, description="ID del cliente", gt=0)
    salesperson_id: Optional[int] = Field(None, description="ID del vendedor", gt=0)
    status: Optional[VisitStatus] = Field(None, description="Estado de la visita")
    
    # Filtros por fecha
    visit_date_from: Optional[date] = Field(None, description="Fecha desde (YYYY-MM-DD)")
    visit_date_to: Optional[date] = Field(None, description="Fecha hasta (YYYY-MM-DD)")
    
    # Filtros por texto
    customer_name: Optional[str] = Field(None, description="Nombre del cliente (búsqueda parcial)")
    salesperson_name: Optional[str] = Field(None, description="Nombre del vendedor (búsqueda parcial)")
    address: Optional[str] = Field(None, description="Dirección (búsqueda parcial)")
    
    # Paginación
    page: int = Field(1, description="Número de página", gt=0)
    per_page: int = Field(20, description="Elementos por página", gt=0, le=100)
    
    # Ordenamiento
    sort_by: Optional[str] = Field("visit_date", description="Campo para ordenar")
    sort_order: Optional[str] = Field("desc", description="Orden: asc o desc")
    
    class Config:
        schema_extra = {
            "example": {
                "customer_id": 1,
                "salesperson_id": 1,
                "status": "SCHEDULED",
                "visit_date_from": "2025-10-01",
                "visit_date_to": "2025-10-31",
                "customer_name": "Hospital",
                "page": 1,
                "per_page": 20,
                "sort_by": "visit_date",
                "sort_order": "desc"
            }
        }
    
    @validator('visit_date_to')
    def validate_date_range(cls, v, values):
        """Validar que fecha_hasta >= fecha_desde"""
        if v and 'visit_date_from' in values and values['visit_date_from']:
            if v < values['visit_date_from']:
                raise ValueError('visit_date_to debe ser mayor o igual a visit_date_from')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validar orden de clasificación"""
        if v and v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order debe ser "asc" o "desc"')
        return v.lower() if v else 'desc'
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validar campo de ordenamiento"""
        valid_fields = [
            'visit_date', 'visit_time', 'created_at', 'updated_at',
            'customer_name', 'salesperson_name', 'status'
        ]
        if v and v not in valid_fields:
            raise ValueError(f'sort_by debe ser uno de: {valid_fields}')
        return v


class VisitStatsResponse(BaseModel):
    """Respuesta con estadísticas de visitas"""
    
    total_visits: int = Field(0, description="Total de visitas")
    scheduled_visits: int = Field(0, description="Visitas programadas")
    completed_visits: int = Field(0, description="Visitas completadas")
    cancelled_visits: int = Field(0, description="Visitas canceladas")
    
    # Estadísticas por período
    visits_today: int = Field(0, description="Visitas de hoy")
    visits_this_week: int = Field(0, description="Visitas esta semana")
    visits_this_month: int = Field(0, description="Visitas este mes")
    
    # Promedio de archivos por visita
    avg_files_per_visit: float = Field(0.0, description="Promedio de archivos por visita")
    
    class Config:
        schema_extra = {
            "example": {
                "total_visits": 150,
                "scheduled_visits": 25,
                "completed_visits": 120,
                "cancelled_visits": 5,
                "visits_today": 3,
                "visits_this_week": 12,
                "visits_this_month": 45,
                "avg_files_per_visit": 2.3
            }
        }


class FileUploadRequest(BaseModel):
    """DTO para solicitud de carga de archivo"""
    
    visit_id: int = Field(..., description="ID de la visita", gt=0)
    file_name: str = Field(..., description="Nombre del archivo", max_length=255)
    mime_type: Optional[str] = Field(None, description="Tipo MIME del archivo")
    file_size: Optional[int] = Field(None, description="Tamaño del archivo en bytes", gt=0)
    
    class Config:
        schema_extra = {
            "example": {
                "visit_id": 1,
                "file_name": "inventory_report.pdf",
                "mime_type": "application/pdf",
                "file_size": 1024000
            }
        }
    
    @validator('file_name')
    def validate_file_name(cls, v):
        """Validar nombre de archivo"""
        if not v or v.strip() == '':
            raise ValueError('file_name no puede estar vacío')
        
        # Validar extensión
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.xlsx', '.xls']
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'Extensión no permitida. Extensiones válidas: {allowed_extensions}')
        
        return v.strip()
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validar tamaño de archivo (máximo 10MB)"""
        if v and v > 10 * 1024 * 1024:  # 10MB
            raise ValueError('El archivo no puede superar 10MB')
        return v


class BulkVisitUpdateRequest(BaseModel):
    """DTO para actualización masiva de visitas"""
    
    visit_ids: List[int] = Field(..., description="Lista de IDs de visitas", min_items=1)
    status: Optional[VisitStatus] = Field(None, description="Nuevo estado")
    salesperson_id: Optional[int] = Field(None, description="Nuevo vendedor", gt=0)
    
    class Config:
        schema_extra = {
            "example": {
                "visit_ids": [1, 2, 3, 4],
                "status": "CANCELLED",
                "salesperson_id": 2
            }
        }
    
    @validator('visit_ids')
    def validate_visit_ids(cls, v):
        """Validar IDs únicos y válidos"""
        if len(v) != len(set(v)):
            raise ValueError('Los IDs de visitas deben ser únicos')
        
        if len(v) > 50:
            raise ValueError('No se pueden actualizar más de 50 visitas a la vez')
        
        return v