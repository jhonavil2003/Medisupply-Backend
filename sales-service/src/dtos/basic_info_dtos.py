from pydantic import BaseModel, Field
from typing import Optional


class CustomerBasicInfo(BaseModel):
    """Información básica del cliente para respuestas anidadas"""
    
    id: int = Field(..., description="ID único del cliente")
    name: str = Field(..., description="Nombre del cliente")
    email: Optional[str] = Field(None, description="Email del cliente")
    phone: Optional[str] = Field(None, description="Teléfono del cliente")
    address: Optional[str] = Field(None, description="Dirección del cliente")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Hospital San José",
                "email": "contacto@hospitalsanjose.com",
                "phone": "+57 1 234-5678",
                "address": "Calle 123 #45-67, Bogotá"
            }
        }


class SalespersonBasicInfo(BaseModel):
    """Información básica del vendedor para respuestas anidadas"""
    
    id: int = Field(..., description="ID único del vendedor")
    name: str = Field(..., description="Nombre completo del vendedor")
    email: Optional[str] = Field(None, description="Email del vendedor")
    phone: Optional[str] = Field(None, description="Teléfono del vendedor")
    territory: Optional[str] = Field(None, description="Territorio asignado")
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Juan Carlos Pérez",
                "email": "juan.perez@medisupply.com",
                "phone": "+57 300 123-4567",
                "territory": "Bogotá Norte"
            }
        }