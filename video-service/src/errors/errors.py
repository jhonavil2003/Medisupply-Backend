"""
Error Handling
==============

Sistema centralizado de manejo de errores para el Video Service.
Replica el patrón de los microservicios Flask existentes.
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """
    Error base de la API.
    
    Usado para errores controlados que deben retornarse al cliente
    con un código HTTP específico.
    
    Attributes:
        message: Mensaje de error para el cliente
        status_code: Código HTTP (default: 400)
        payload: Información adicional opcional
    """
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        """Convierte el error a diccionario serializable"""
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class ValidationError(ApiError):
    """
    Error de validación de datos.
    
    Usado cuando los datos de entrada no cumplen los requisitos.
    Siempre retorna 400 Bad Request.
    """
    status_code = 400


class NotFoundError(ApiError):
    """
    Error de recurso no encontrado.
    
    Usado cuando un recurso solicitado no existe.
    Siempre retorna 404 Not Found.
    """
    status_code = 404


class DatabaseError(ApiError):
    """
    Error de base de datos.
    
    Usado para errores relacionados con operaciones de BD.
    Siempre retorna 500 Internal Server Error.
    """
    status_code = 500


class ExternalServiceError(ApiError):
    """
    Error de servicio externo.
    
    Usado cuando un servicio externo (RAG, Gemini, etc.) falla.
    Retorna 502 Bad Gateway o 500 según contexto.
    """
    status_code = 502


def register_error_handlers(app):
    """
    Registra manejadores de errores con la aplicación Flask.
    
    PATRÓN CLONADO de catalog-service/src/errors/errors.py
    
    Maneja:
    - Errores custom (ApiError y subclases)
    - Errores HTTP de Werkzeug
    - Excepciones genéricas de Python
    
    Args:
        app: Instancia de Flask
    """
    
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        """Maneja errores ApiError y subclases"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.warning(
            f"API Error {error.status_code}: {error.message}",
            extra={'status_code': error.status_code}
        )
        return response
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Maneja errores de validación específicamente"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.info(
            f"Validation Error: {error.message}",
            extra={'status_code': 400}
        )
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        """Maneja errores 404 Not Found"""
        return jsonify({
            'error': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        """Maneja errores 400 Bad Request"""
        return jsonify({
            'error': 'Bad request',
            'status_code': 400,
            'message': str(error)
        }), 400
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Maneja errores 500 Internal Server Error"""
        logger.error(f"Internal Server Error: {str(error)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500,
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Maneja excepciones HTTP de Werkzeug"""
        return jsonify({
            'error': error.name,
            'status_code': error.code,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Maneja excepciones genéricas no capturadas"""
        logger.error(
            f'Unhandled exception: {str(error)}',
            exc_info=True,
            extra={'error_type': type(error).__name__}
        )
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500,
            'message': 'An unexpected error occurred'
        }), 500
    
    logger.info("Error handlers registered successfully")
