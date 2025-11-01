from pydantic import BaseModel, Field, validator
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from src.entities.visit_status import VisitStatus


class CreateVisitRequest(BaseModel):
    """DTO para crear una nueva visita"""
    
    customer_id: int = Field(..., description="ID del cliente", gt=0)
    salesperson_id: int = Field(..., description="ID del vendedor", gt=0)
    visit_date: date = Field(..., description="Fecha de visita (YYYY-MM-DD)")
    visit_time: time = Field(..., description="Hora de visita (HH:MM:SS)")
    
    # Campos opcionales
    contacted_persons: Optional[str] = Field(None, description="Personas contactadas", max_length=1000)
    clinical_findings: Optional[str] = Field(None, description="Hallazgos clínicos", max_length=2000)
    additional_notes: Optional[str] = Field(None, description="Notas adicionales", max_length=2000)
    address: Optional[str] = Field(None, description="Dirección de visita", max_length=500)
    
    # Coordenadas GPS con validación
    latitude: Optional[Decimal] = Field(None, description="Latitud", ge=-90.0, le=90.0)
    longitude: Optional[Decimal] = Field(None, description="Longitud", ge=-180.0, le=180.0)
    
    class Config:
        # Configuración para serialización JSON
        json_encoders = {
            date: lambda v: v.isoformat(),
            time: lambda v: v.strftime("%H:%M:%S"),
            Decimal: lambda v: float(v) if v else None
        }
        schema_extra = {
            "example": {
                "customer_id": 1,
                "salesperson_id": 2,
                "visit_date": "2025-10-30",
                "visit_time": "14:30:00",
                "contacted_persons": "Dr. María González, Jefe de Compras",
                "clinical_findings": "Necesitan reposición de inventario de jeringas",
                "additional_notes": "Cliente interesado en nuevos productos ortopédicos",
                "address": "Calle 10 #5-25, Bogotá",
                "latitude": 4.60971,
                "longitude": -74.08175
            }
        }
    
    @validator('visit_date')
    def validate_visit_date(cls, v):
        """Validar que la fecha no sea en el pasado"""
        if v < date.today():
            raise ValueError('La fecha de visita no puede ser en el pasado')
        return v
    
    @validator('visit_time')
    def validate_visit_time(cls, v):
        """Validar horario laboral"""
        if v.hour < 6 or v.hour > 20:
            raise ValueError('Las visitas deben programarse entre 6:00 AM y 8:00 PM')
        return v
    
    def to_dict(self) -> dict:
        """Convierte el DTO a diccionario"""
        return {
            'customer_id': self.customer_id,
            'salesperson_id': self.salesperson_id,
            'visit_date': self.visit_date,
            'visit_time': self.visit_time,
            'contacted_persons': self.contacted_persons,
            'clinical_findings': self.clinical_findings,
            'additional_notes': self.additional_notes,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude
        }