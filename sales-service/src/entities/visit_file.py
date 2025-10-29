from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.session import Base
from datetime import datetime
from typing import Optional


class VisitFile(Base):
    """Entidad VisitFile - Representa un archivo adjunto a una visita"""
    
    __tablename__ = 'visit_files'

    # Primary Key
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    visit_id: int = Column(Integer, ForeignKey('visits.id'), nullable=False)
    
    # File Information
    file_name: str = Column(String(255), nullable=False)
    file_path: str = Column(String(500), nullable=False)
    file_size: Optional[int] = Column(Integer, nullable=True)
    mime_type: Optional[str] = Column(String(100), nullable=True)
    file_data: Optional[bytes] = Column(LargeBinary, nullable=True)
    
    # Timestamps
    uploaded_at: datetime = Column(DateTime, default=func.now(), nullable=False)

    # Relationships - Lazy loading similar to JPA
    visit = relationship("Visit", back_populates="files", lazy="select")

    def __init__(self, visit_id: int = None, file_name: str = None, 
                 file_path: str = None, file_size: int = None,
                 mime_type: str = None, file_data: bytes = None):
        """Constructor similar a Java"""
        self.visit_id = visit_id
        self.file_name = file_name
        self.file_path = file_path
        self.file_size = file_size
        self.mime_type = mime_type
        self.file_data = file_data

    def __repr__(self):
        return f"<VisitFile(id={self.id}, visit_id={self.visit_id}, file_name='{self.file_name}')>"

    # Getters and Setters (Java style)
    def get_id(self) -> Optional[int]:
        return self.id
    
    def set_id(self, id: int):
        self.id = id
    
    def get_visit_id(self) -> int:
        return self.visit_id
    
    def set_visit_id(self, visit_id: int):
        self.visit_id = visit_id
    
    def get_file_name(self) -> str:
        return self.file_name
    
    def set_file_name(self, file_name: str):
        self.file_name = file_name
    
    def get_file_path(self) -> str:
        return self.file_path
    
    def set_file_path(self, file_path: str):
        self.file_path = file_path
    
    def get_file_size(self) -> Optional[int]:
        return self.file_size
    
    def set_file_size(self, file_size: int):
        self.file_size = file_size
    
    def get_mime_type(self) -> Optional[str]:
        return self.mime_type
    
    def set_mime_type(self, mime_type: str):
        self.mime_type = mime_type
    
    def get_file_data(self) -> Optional[bytes]:
        return self.file_data
    
    def set_file_data(self, file_data: bytes):
        self.file_data = file_data
    
    def get_visit(self):
        return self.visit
    
    def set_visit(self, visit):
        self.visit = visit
        if visit:
            self.visit_id = visit.id
    
    def get_uploaded_at(self) -> datetime:
        return self.uploaded_at

    # Business Methods
    def get_file_size_formatted(self) -> str:
        """Retorna el tamaño del archivo en formato legible"""
        if not self.file_size:
            return "0 B"
            
        size = self.file_size
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
            
        return f"{size:.1f} {units[unit_index]}"
    
    def is_image(self) -> bool:
        """Verifica si el archivo es una imagen"""
        if not self.mime_type:
            return False
        return self.mime_type.startswith('image/')
    
    def is_document(self) -> bool:
        """Verifica si el archivo es un documento"""
        if not self.mime_type:
            return False
        document_types = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        return self.mime_type in document_types

    def to_dict(self, include_data: bool = False) -> dict:
        """Convierte la entidad a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'visit_id': self.visit_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_formatted': self.get_file_size_formatted(),
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_image': self.is_image(),
            'is_document': self.is_document()
        }
        
        # Solo incluir datos binarios si se solicita explícitamente
        if include_data and self.file_data:
            import base64
            result['file_data'] = base64.b64encode(self.file_data).decode('utf-8')
            
        return result