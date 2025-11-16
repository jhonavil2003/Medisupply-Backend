from flask import jsonify
from werkzeug.exceptions import HTTPException

class ApiError(Exception):
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv
    
    def __str__(self):
        return self.message

class NotFoundError(ApiError):
    """Resource not found error"""
    status_code = 404

class ValidationError(ApiError):
    """Validation error"""
    status_code = 400

class ConflictError(ApiError):
    """Conflict error (e.g., insufficient stock, duplicate resource)"""
    status_code = 409

def register_error_handlers(app):
    """Register error handlers with Flask app"""
    
    @app.errorhandler(ApiError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Resource not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'status_code': 400,
            'message': str(error)
        }), 400
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500,
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'error': error.name,
            'status_code': error.code,
            'message': error.description
        }), error.code
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        app.logger.error(f'Unhandled exception: {str(error)}')
        return jsonify({
            'error': 'Internal server error',
            'status_code': 500,
            'message': 'An unexpected error occurred'
        }), 500
