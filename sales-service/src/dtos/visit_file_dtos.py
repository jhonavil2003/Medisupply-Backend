from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional


class VisitFileResponse(BaseModel):
    """DTO de respuesta para archivos de visitas"""
    
    id: int = Field(..., description="ID único del archivo")
    visit_id: int = Field(..., description="ID de la visita asociada")
    file_name: str = Field(..., description="Nombre original del archivo")
    file_path: str = Field(..., description="Ruta del archivo en el servidor")
    file_size: int = Field(..., description="Tamaño del archivo en bytes")
    mime_type: str = Field(..., description="Tipo MIME del archivo")
    uploaded_at: datetime = Field(..., description="Fecha y hora de subida")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "id": 1,
                "visit_id": 123,
                "file_name": "inventory_report.pdf",
                "file_path": "/uploads/visits/123/inventory_report_20241029_143022.pdf",
                "file_size": 2048576,
                "mime_type": "application/pdf",
                "uploaded_at": "2024-10-29T14:30:22"
            }
        }


class VisitFileUploadRequest(BaseModel):
    """DTO para solicitud de subida de archivo (metadatos)"""
    
    visit_id: int = Field(..., description="ID de la visita", gt=0)
    file_name: str = Field(..., description="Nombre del archivo", max_length=255)
    file_size: Optional[int] = Field(None, description="Tamaño del archivo en bytes", gt=0)
    mime_type: Optional[str] = Field(None, description="Tipo MIME del archivo")
    
    class Config:
        schema_extra = {
            "example": {
                "visit_id": 123,
                "file_name": "contract_signed.pdf",
                "file_size": 1024000,
                "mime_type": "application/pdf"
            }
        }
    
    @validator('file_name')
    def validate_file_name(cls, v):
        """Validar nombre de archivo"""
        if not v or v.strip() == '':
            raise ValueError('file_name no puede estar vacío')
        
        # Validar extensión
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.rtf',  # Documentos
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',  # Imágenes
            '.xlsx', '.xls', '.csv',                  # Hojas de cálculo
            '.zip', '.rar'                            # Archivos comprimidos
        ]
        
        if not any(v.lower().endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'Extensión no permitida. Extensiones válidas: {allowed_extensions}')
        
        return v.strip()
    
    @validator('file_size')
    def validate_file_size(cls, v):
        """Validar tamaño de archivo (máximo 10MB)"""
        if v and v > 10 * 1024 * 1024:  # 10MB
            raise ValueError('El archivo no puede superar 10MB')
        return v


class VisitFileListResponse(BaseModel):
    """DTO para lista de archivos de una visita"""
    
    visit_id: int = Field(..., description="ID de la visita")
    files: list[VisitFileResponse] = Field(default_factory=list, description="Lista de archivos")
    total_files: int = Field(0, description="Total de archivos")
    total_size: int = Field(0, description="Tamaño total en bytes")
    
    class Config:
        schema_extra = {
            "example": {
                "visit_id": 123,
                "files": [
                    {
                        "id": 1,
                        "visit_id": 123,
                        "file_name": "inventory_report.pdf",
                        "file_path": "/uploads/visits/123/inventory_report.pdf",
                        "file_size": 2048576,
                        "mime_type": "application/pdf",
                        "uploaded_at": "2024-10-29T14:30:22"
                    }
                ],
                "total_files": 1,
                "total_size": 2048576
            }
        }


class FileUploadResponse(BaseModel):
    """DTO de respuesta para confirmación de subida de archivo"""
    
    success: bool = Field(..., description="Indica si la subida fue exitosa")
    message: str = Field(..., description="Mensaje de respuesta")
    file: Optional[VisitFileResponse] = Field(None, description="Información del archivo subido")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Archivo subido exitosamente",
                "file": {
                    "id": 1,
                    "visit_id": 123,
                    "file_name": "contract.pdf",
                    "file_path": "/uploads/visits/123/contract.pdf",
                    "file_size": 1024000,
                    "mime_type": "application/pdf",
                    "uploaded_at": "2024-10-29T14:30:22"
                }
            }
        }


class FileDeleteResponse(BaseModel):
    """DTO de respuesta para eliminación de archivo"""
    
    success: bool = Field(..., description="Indica si la eliminación fue exitosa")
    message: str = Field(..., description="Mensaje de respuesta")
    deleted_file_id: int = Field(..., description="ID del archivo eliminado")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Archivo eliminado exitosamente",
                "deleted_file_id": 1
            }
        }