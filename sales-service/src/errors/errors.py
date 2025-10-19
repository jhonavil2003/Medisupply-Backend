from flask import jsonify


class ApiError(Exception):
    """Base class for API errors."""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def __str__(self):
        return self.message
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv


class NotFoundError(ApiError):
    """Raised when a resource is not found."""
    
    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)


class ValidationError(ApiError):
    """Raised when request validation fails."""
    
    def __init__(self, message="Validation error", payload=None):
        super().__init__(message, status_code=400, payload=payload)


class StockValidationError(ApiError):
    """Raised when stock validation fails."""
    
    def __init__(self, message="Insufficient stock", payload=None):
        super().__init__(message, status_code=409, payload=payload)


class ExternalServiceError(ApiError):
    """Raised when an external service call fails."""
    
    def __init__(self, message="External service error", payload=None):
        super().__init__(message, status_code=503, payload=payload)


def handle_api_error(error):
    """Handle ApiError exceptions."""
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def handle_404(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Resource not found',
        'status_code': 404
    }), 404


def handle_500(error):
    """Handle 500 errors."""
    return jsonify({
        'error': 'Internal server error',
        'status_code': 500
    }), 500


def register_error_handlers(app):
    """Register error handlers with the Flask app."""
    app.register_error_handler(ApiError, handle_api_error)
    app.register_error_handler(404, handle_404)
    app.register_error_handler(500, handle_500)
