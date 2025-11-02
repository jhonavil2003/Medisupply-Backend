"""
Blueprint para manejo de archivos de visitas
Endpoints para subir, listar y eliminar archivos adjuntos a visitas
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, NotFound
import os
import uuid
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from src.dtos import (
    VisitFileResponse,
    VisitFileUploadRequest,
    VisitFileListResponse,
    FileUploadResponse,
    FileDeleteResponse
)
from src.session import db
from src.entities.visit_file import VisitFile
from src.entities.visit import Visit
from src.errors.errors import NotFoundError, ValidationError

# Crear el blueprint
visit_files_bp = Blueprint('visit_files', __name__, url_prefix='/visits')

# Configuración de archivos
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.xlsx', '.xls', '.csv', '.zip', '.rar'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def upload_visit_file(file_data: VisitFileUploadRequest, file_path: str, stored_filename: str) -> VisitFileResponse:
    """Guardar información del archivo en la base de datos"""
    # Verificar que la visita existe  
    visit = db.session.query(Visit).filter(Visit.id == file_data.visit_id).first()
    if not visit:
        raise NotFoundError(f"La visita con ID {file_data.visit_id} no existe")
    
    # Crear registro del archivo
    visit_file = VisitFile(
        visit_id=file_data.visit_id,
        file_name=file_data.file_name,
        file_path=file_path,
        file_size=file_data.file_size,
        mime_type=file_data.mime_type,
        uploaded_at=datetime.utcnow()
    )
    
    db.session.add(visit_file)
    db.session.commit()
    db.session.refresh(visit_file)
    
    return VisitFileResponse(
        id=visit_file.id,
        visit_id=visit_file.visit_id,
        file_name=visit_file.file_name,
        file_path=visit_file.file_path,
        file_size=visit_file.file_size,
        mime_type=visit_file.mime_type,
        uploaded_at=visit_file.uploaded_at
    )


def get_files_by_visit(visit_id: int) -> List[VisitFileResponse]:
    """Obtener todos los archivos de una visita"""
    # Verificar que la visita existe
    visit = db.session.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        raise NotFoundError(f"La visita con ID {visit_id} no existe")
    
    # Obtener archivos de la visita
    files = db.session.query(VisitFile).filter(
        VisitFile.visit_id == visit_id
    ).order_by(VisitFile.uploaded_at.desc()).all()
    
    return [
        VisitFileResponse(
            id=file.id,
            visit_id=file.visit_id,
            file_name=file.file_name,
            file_path=file.file_path,
            file_size=file.file_size,
            mime_type=file.mime_type,
            uploaded_at=file.uploaded_at
        )
        for file in files
    ]


def get_file_by_id(file_id: int, visit_id: int) -> VisitFileResponse:
    """Obtener un archivo específico por ID"""
    try:
        file = db.session.query(VisitFile).filter(
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
            uploaded_at=file.uploaded_at
        )
    except NoResultFound:
        raise NotFoundError(f"El archivo con ID {file_id} no existe en la visita {visit_id}")


def delete_visit_file(file_id: int, visit_id: int) -> bool:
    """Eliminar un archivo de la base de datos"""
    try:
        file = db.session.query(VisitFile).filter(
            VisitFile.id == file_id,
            VisitFile.visit_id == visit_id
        ).one()
        
        db.session.delete(file)
        db.session.commit()
        return True
    except NoResultFound:
        raise NotFoundError(f"El archivo con ID {file_id} no existe en la visita {visit_id}")


def allowed_file(filename: str) -> bool:
    """Verificar si la extensión del archivo está permitida"""
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)


def generate_unique_filename(original_filename: str) -> str:
    """Generar nombre único para el archivo"""
    name, ext = os.path.splitext(secure_filename(original_filename))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    return f"{name}_{timestamp}_{unique_id}{ext}"


@visit_files_bp.route('/<int:visit_id>/files', methods=['POST'])
def upload_file(visit_id: int):
    """
    📎 Subir archivo a una visita (desde tab "Archivos")
    
    Args:
        visit_id: ID de la visita
        file: Archivo multipart
    
    Returns:
        VisitFileResponse: Información del archivo subido
    """
    try:
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            raise BadRequest('No se envió ningún archivo')
        
        file = request.files['file']
        
        # Verificar que el archivo tiene nombre
        if file.filename == '':
            raise BadRequest('No se seleccionó ningún archivo')
        
        # Verificar extensión permitida
        if not allowed_file(file.filename):
            raise BadRequest(f'Extensión no permitida. Extensiones válidas: {list(ALLOWED_EXTENSIONS)}')
        
        # Verificar tamaño del archivo
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise BadRequest('El archivo no puede superar 10MB')
        
        # Generar nombre único
        unique_filename = generate_unique_filename(file.filename)
        
        # Crear directorio para la visita si no existe
        upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'visits', str(visit_id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Ruta completa del archivo
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Guardar archivo
        file.save(file_path)
        
        # Crear registro en base de datos
        file_data = VisitFileUploadRequest(
            visit_id=visit_id,
            file_name=file.filename,
            file_size=file_size,
            mime_type=file.content_type or 'application/octet-stream'
        )
        
        # Guardar en BD y obtener respuesta
        file_response = upload_visit_file(file_data, file_path, unique_filename)
        
        # Respuesta exitosa
        response = FileUploadResponse(
            success=True,
            message="Archivo subido exitosamente",
            file=file_response
        )
        
        return jsonify(response.dict()), 201
        
    except (BadRequest, ValidationError) as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "file": None
        }), 400
    except NotFoundError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "file": None
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor",
            "file": None
        }), 500


@visit_files_bp.route('/<int:visit_id>/files', methods=['GET'])
def get_files_by_visit_endpoint(visit_id: int):
    """
    📋 Listar archivos de una visita
    
    Args:
        visit_id: ID de la visita
    
    Returns:
        List[VisitFileResponse]: Lista de archivos de la visita
    """
    try:
        # Obtener archivos de la visita
        files = get_files_by_visit(visit_id)
        
        # Si se quiere respuesta detallada con metadatos
        include_metadata = request.args.get('include_metadata', 'false').lower() == 'true'
        
        if include_metadata:
            # Calcular estadísticas
            total_size = sum(file.file_size for file in files)
            
            response = VisitFileListResponse(
                visit_id=visit_id,
                files=files,
                total_files=len(files),
                total_size=total_size
            )
            return jsonify(response.dict()), 200
        else:
            # Respuesta simple (lista de archivos)
            return jsonify([file.dict() for file in files]), 200
        
    except NotFoundError as e:
        return jsonify({
            "error": "Not Found",
            "message": str(e)
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error getting files for visit {visit_id}: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "Error interno del servidor"
        }), 500


@visit_files_bp.route('/<int:visit_id>/files/<int:file_id>', methods=['DELETE'])
def delete_file_endpoint(visit_id: int, file_id: int):
    """
    🗑️ Eliminar archivo
    
    Args:
        visit_id: ID de la visita
        file_id: ID del archivo
    
    Returns:
        FileDeleteResponse: Confirmación de eliminación
    """
    try:
        # Verificar que el archivo existe y pertenece a la visita
        file_info = get_file_by_id(file_id, visit_id)
        
        # Eliminar archivo físico
        if os.path.exists(file_info.file_path):
            os.remove(file_info.file_path)
        
        # Eliminar registro de la base de datos
        delete_visit_file(file_id, visit_id)
        
        # Respuesta exitosa
        response = FileDeleteResponse(
            success=True,
            message="Archivo eliminado exitosamente",
            deleted_file_id=file_id
        )
        
        return jsonify(response.dict()), 200
        
    except NotFoundError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "deleted_file_id": file_id
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting file {file_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor",
            "deleted_file_id": file_id
        }), 500


@visit_files_bp.route('/<int:visit_id>/files/<int:file_id>/download', methods=['GET'])
def download_file(visit_id: int, file_id: int):
    """
    📥 Descargar archivo
    
    Args:
        visit_id: ID de la visita
        file_id: ID del archivo
    
    Returns:
        File: Archivo para descarga
    """
    try:
        from flask import send_file
        
        # Obtener información del archivo
        file_info = get_file_by_id(file_id, visit_id)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_info.file_path):
            raise NotFoundError("El archivo no existe en el servidor")
        
        # Enviar archivo
        return send_file(
            file_info.file_path,
            as_attachment=True,
            download_name=file_info.file_name,
            mimetype=file_info.mime_type
        )
        
    except NotFoundError as e:
        return jsonify({
            "error": "Not Found",
            "message": str(e)
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error downloading file {file_id}: {str(e)}")
        return jsonify({
            "error": "Internal Server Error", 
            "message": "Error interno del servidor"
        }), 500


# Crear el blueprint para rutas globales de archivos (como espera el frontend)
files_bp = Blueprint('files', __name__, url_prefix='/visits/files')

@files_bp.route('/<int:file_id>', methods=['DELETE'])
def delete_file_global(file_id: int):
    """
    🗑️ Eliminar archivo (ruta global como espera el frontend)
    
    Args:
        file_id: ID del archivo
    
    Returns:
        FileDeleteResponse: Confirmación de eliminación
    """
    try:
        # Obtener el archivo para saber a qué visita pertenece
        file = db.session.query(VisitFile).filter(VisitFile.id == file_id).first()
        if not file:
            raise NotFoundError(f"El archivo con ID {file_id} no existe")
        
        visit_id = file.visit_id
        
        # Eliminar archivo físico
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Eliminar registro de la base de datos
        db.session.delete(file)
        db.session.commit()
        
        # Respuesta exitosa
        response = FileDeleteResponse(
            success=True,
            message="Archivo eliminado exitosamente",
            deleted_file_id=file_id
        )
        
        return jsonify(response.dict()), 200
        
    except NotFoundError as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "deleted_file_id": file_id
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting file {file_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": "Error interno del servidor",
            "deleted_file_id": file_id
        }), 500


# Endpoint adicional para obtener estadísticas de archivos
@visit_files_bp.route('/<int:visit_id>/files/stats', methods=['GET'])
def get_files_stats(visit_id: int):
    """
    📊 Obtener estadísticas de archivos de una visita
    
    Args:
        visit_id: ID de la visita
    
    Returns:
        dict: Estadísticas de archivos
    """
    try:
        files = get_files_by_visit(visit_id)
        
        # Calcular estadísticas
        total_files = len(files)
        total_size = sum(file.file_size for file in files)
        
        # Agrupar por tipo de archivo
        file_types = {}
        for file in files:
            mime_type = file.mime_type
            if mime_type in file_types:
                file_types[mime_type]['count'] += 1
                file_types[mime_type]['size'] += file.file_size
            else:
                file_types[mime_type] = {'count': 1, 'size': file.file_size}
        
        stats = {
            'visit_id': visit_id,
            'total_files': total_files,
            'total_size': total_size,
            'average_size': total_size / total_files if total_files > 0 else 0,
            'file_types': file_types
        }
        
        return jsonify(stats), 200
        
    except NotFoundError as e:
        return jsonify({
            "error": "Not Found",
            "message": str(e)
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error getting file stats for visit {visit_id}: {str(e)}")
        return jsonify({
            "error": "Internal Server Error",
            "message": "Error interno del servidor"
        }), 500