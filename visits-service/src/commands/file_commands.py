"""
Comandos para manejo de archivos de visitas
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.session import create_session
from src.entities.visit_file import VisitFile
from src.entities.visit import Visit
from src.dtos import VisitFileResponse, VisitFileUploadRequest
from src.errors.errors import NotFoundError, ValidationError


def upload_visit_file(file_data: VisitFileUploadRequest, file_path: str, stored_filename: str) -> VisitFileResponse:
    """
    Guardar información del archivo en la base de datos
    
    Args:
        file_data: Datos del archivo
        file_path: Ruta donde se guardó el archivo
        stored_filename: Nombre con el que se guardó el archivo
    
    Returns:
        VisitFileResponse: Información del archivo creado
    
    Raises:
        NotFoundError: Si la visita no existe
        ValidationError: Si los datos son inválidos
    """
    with create_session() as session:
        # Verificar que la visita existe
        visit = session.query(Visit).filter(Visit.id == file_data.visit_id).first()
        if not visit:
            raise NotFoundError(f"La visita con ID {file_data.visit_id} no existe")
        
        # Crear registro del archivo
        visit_file = VisitFile(
            visit_id=file_data.visit_id,
            file_name=file_data.file_name,
            file_path=file_path,
            file_size=file_data.file_size,
            mime_type=file_data.mime_type,
            upload_date=datetime.utcnow()
        )
        
        session.add(visit_file)
        session.commit()
        session.refresh(visit_file)
        
        # Convertir a DTO de respuesta
        return VisitFileResponse(
            id=visit_file.id,
            visit_id=visit_file.visit_id,
            file_name=visit_file.file_name,
            file_path=visit_file.file_path,
            file_size=visit_file.file_size,
            mime_type=visit_file.mime_type,
            upload_date=visit_file.upload_date
        )


def get_files_by_visit(visit_id: int) -> List[VisitFileResponse]:
    """
    Obtener todos los archivos de una visita
    
    Args:
        visit_id: ID de la visita
    
    Returns:
        List[VisitFileResponse]: Lista de archivos
    
    Raises:
        NotFoundError: Si la visita no existe
    """
    with create_session() as session:
        # Verificar que la visita existe
        visit = session.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise NotFoundError(f"La visita con ID {visit_id} no existe")
        
        # Obtener archivos de la visita
        files = session.query(VisitFile).filter(
            VisitFile.visit_id == visit_id
        ).order_by(VisitFile.upload_date.desc()).all()
        
        # Convertir a DTOs de respuesta
        return [
            VisitFileResponse(
                id=file.id,
                visit_id=file.visit_id,
                file_name=file.file_name,
                file_path=file.file_path,
                file_size=file.file_size,
                mime_type=file.mime_type,
                upload_date=file.upload_date
            )
            for file in files
        ]


def get_file_by_id(file_id: int, visit_id: int) -> VisitFileResponse:
    """
    Obtener un archivo específico por ID
    
    Args:
        file_id: ID del archivo
        visit_id: ID de la visita (para verificar pertenencia)
    
    Returns:
        VisitFileResponse: Información del archivo
    
    Raises:
        NotFoundError: Si el archivo no existe o no pertenece a la visita
    """
    with create_session() as session:
        try:
            file = session.query(VisitFile).filter(
                VisitFile.id == file_id,
                VisitFile.visit_id == visit_id
            ).one()
            
            return VisitFileResponse(
                id=file.id,
                visit_id=file.visit_id,
                file_name=file.file_name,
                file_path=file.file_path,
                file_size=file.file_size,
                mime_type=file.mime_type,
                upload_date=file.upload_date
            )
            
        except NoResultFound:
            raise NotFoundError(f"El archivo con ID {file_id} no existe en la visita {visit_id}")


def delete_visit_file(file_id: int, visit_id: int) -> bool:
    """
    Eliminar un archivo de la base de datos
    
    Args:
        file_id: ID del archivo
        visit_id: ID de la visita (para verificar pertenencia)
    
    Returns:
        bool: True si se eliminó correctamente
    
    Raises:
        NotFoundError: Si el archivo no existe o no pertenece a la visita
    """
    with create_session() as session:
        try:
            file = session.query(VisitFile).filter(
                VisitFile.id == file_id,
                VisitFile.visit_id == visit_id
            ).one()
            
            session.delete(file)
            session.commit()
            return True
            
        except NoResultFound:
            raise NotFoundError(f"El archivo con ID {file_id} no existe en la visita {visit_id}")


def get_files_count_by_visit(visit_id: int) -> int:
    """
    Obtener el número de archivos de una visita
    
    Args:
        visit_id: ID de la visita
    
    Returns:
        int: Número de archivos
    """
    with create_session() as session:
        count = session.query(VisitFile).filter(
            VisitFile.visit_id == visit_id
        ).count()
        
        return count


def get_total_files_size_by_visit(visit_id: int) -> int:
    """
    Obtener el tamaño total de archivos de una visita
    
    Args:
        visit_id: ID de la visita
    
    Returns:
        int: Tamaño total en bytes
    """
    with create_session() as session:
        files = session.query(VisitFile).filter(
            VisitFile.visit_id == visit_id
        ).all()
        
        return sum(file.file_size for file in files if file.file_size)


def delete_all_files_by_visit(visit_id: int) -> int:
    """
    Eliminar todos los archivos de una visita
    
    Args:
        visit_id: ID de la visita
    
    Returns:
        int: Número de archivos eliminados
    """
    with create_session() as session:
        count = session.query(VisitFile).filter(
            VisitFile.visit_id == visit_id
        ).delete()
        
        session.commit()
        return count