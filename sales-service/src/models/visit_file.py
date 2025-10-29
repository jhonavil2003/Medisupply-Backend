from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from session import Base


class VisitFile(Base):
    __tablename__ = 'visit_files'

    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey('visits.id', ondelete='CASCADE'), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_path = Column(String(500), nullable=True)  # Path for file storage
    file_data = Column(LargeBinary, nullable=True)  # Binary data if storing in DB
    uploaded_at = Column(DateTime, default=func.now(), nullable=False)

    # Relaciones
    visit = relationship("Visit", back_populates="visit_files")

    def __repr__(self):
        return f"<VisitFile(id={self.id}, visit_id={self.visit_id}, file_name='{self.file_name}')>"

    def to_dict(self, include_data=False):
        """Convierte el modelo a diccionario para serialización JSON"""
        result = {
            'id': self.id,
            'visit_id': self.visit_id,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_path': self.file_path,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
        }
        
        # Solo incluir datos binarios si se solicita explícitamente
        if include_data and self.file_data:
            import base64
            result['file_data'] = base64.b64encode(self.file_data).decode('utf-8')
            
        return result

    @staticmethod
    def from_dict(data):
        """Crea una instancia de VisitFile desde un diccionario"""
        visit_file = VisitFile()
        visit_file.visit_id = data.get('visit_id')
        visit_file.file_name = data.get('file_name')
        visit_file.file_type = data.get('file_type')
        visit_file.file_size = data.get('file_size')
        visit_file.file_path = data.get('file_path')
        
        # Manejo de datos binarios
        file_data = data.get('file_data')
        if file_data and isinstance(file_data, str):
            import base64
            visit_file.file_data = base64.b64decode(file_data)
        elif file_data:
            visit_file.file_data = file_data
            
        return visit_file

    def get_file_size_formatted(self):
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