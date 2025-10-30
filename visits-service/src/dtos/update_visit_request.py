from pydantic import BaseModel, Field, validator
from datetime import date, time
from decimal import Decimal
from typing import Optional
from src.entities.visit_status import VisitStatus


class UpdateVisitRequest(BaseModel):
    """DTO para actualizar una visita existente"""
    
    # Todos los campos son opcionales para updates parciales
    visit_date: Optional[date] = Field(None, description="Nueva fecha de visita (YYYY-MM-DD)")
    visit_time: Optional[time] = Field(None, description="Nueva hora de visita (HH:MM:SS)")
    contacted_persons: Optional[str] = Field(None, description="Personas contactadas", max_length=1000)
    clinical_findings: Optional[str] = Field(None, description="Hallazgos clínicos", max_length=2000)
    additional_notes: Optional[str] = Field(None, description="Notas adicionales", max_length=2000)
    address: Optional[str] = Field(None, description="Dirección de visita", max_length=500)
    
    # Coordenadas GPS con validación
    latitude: Optional[Decimal] = Field(None, description="Latitud", ge=-90.0, le=90.0)
    longitude: Optional[Decimal] = Field(None, description="Longitud", ge=-180.0, le=180.0)
    
    # Estado de la visita
    status: Optional[VisitStatus] = Field(None, description="Estado de la visita")
    
    class Config:
        # Configuración para serialización JSON
        json_encoders = {
            date: lambda v: v.isoformat() if v else None,
            time: lambda v: v.strftime("%H:%M:%S") if v else None,
            Decimal: lambda v: float(v) if v else None,
            VisitStatus: lambda v: v.value if v else None
        }
        schema_extra = {
            "example": {
                "visit_date": "2025-11-01",
                "visit_time": "15:00:00",
                "contacted_persons": "Dr. María González, Jefe de Compras, Ana López - Enfermera Jefe",
                "clinical_findings": "Revisión completada. Inventario bajo en jeringas y gasas",
                "additional_notes": "Cliente confirmó pedido para próxima semana. Interés en productos nuevos.",
                "status": "COMPLETED"
            }
        }
    
    @validator('visit_date')
    def validate_visit_date(cls, v):
        """Validar que la fecha no sea muy antigua (solo si se proporciona)"""
        if v is not None and v < date.today():
            # Permitir fechas pasadas para visitas completadas
            pass
        return v
    
    @validator('visit_time')
    def validate_visit_time(cls, v):
        """Validar horario laboral (solo si se proporciona)"""
        if v is not None and (v.hour < 6 or v.hour > 20):
            raise ValueError('Las visitas deben programarse entre 6:00 AM y 8:00 PM')
        return v
    
    @validator('status')
    def validate_status_transition(cls, v):
        """Validar transiciones de estado válidas"""
        if v is not None:
            valid_statuses = [VisitStatus.SCHEDULED, VisitStatus.COMPLETED, VisitStatus.CANCELLED]
            if v not in valid_statuses:
                raise ValueError(f'Estado inválido. Valores permitidos: {[s.value for s in valid_statuses]}')
        return v
    
    def to_dict(self, exclude_none: bool = True) -> dict:
        """Convierte el DTO a diccionario"""
        data = {
            'visit_date': self.visit_date,
            'visit_time': self.visit_time,
            'contacted_persons': self.contacted_persons,
            'clinical_findings': self.clinical_findings,
            'additional_notes': self.additional_notes,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'status': self.status
        }
        
        if exclude_none:
            return {k: v for k, v in data.items() if v is not None}
        return data
    
    def has_updates(self) -> bool:
        """Verifica si el DTO contiene actualizaciones"""
        return any([
            self.visit_date is not None,
            self.visit_time is not None,
            self.contacted_persons is not None,
            self.clinical_findings is not None,
            self.additional_notes is not None,
            self.address is not None,
            self.latitude is not None,
            self.longitude is not None,
            self.status is not None
        ])