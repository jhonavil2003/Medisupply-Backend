"""
Blueprint para endpoints de reservas de carrito de compra.

Endpoints:
- POST /cart/reserve - Reservar stock temporalmente
- POST /cart/release - Liberar stock reservado
- DELETE /cart/clear - Limpiar todo el carrito de un usuario
- GET /cart/reservations - Obtener reservas activas de un usuario
"""

from flask import Blueprint, request, jsonify
from src.commands.cart_reservations import (
    ReserveStockCommand,
    ReleaseStockCommand,
    ClearUserCartReservationsCommand
)
from src.commands.get_realtime_stock import GetRealTimeStock
from src.errors.errors import ValidationError, NotFoundError, ConflictError
import logging

logger = logging.getLogger(__name__)

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')


@cart_bp.route('/reserve', methods=['POST'])
def reserve_stock():
    """
    POST /cart/reserve
    
    Reserva stock temporalmente cuando un usuario agrega productos al carrito.
    
    Body (JSON):
    {
        "product_sku": "JER-001",
        "quantity": 2,
        "user_id": "user123",
        "session_id": "sess-uuid-456",
        "distribution_center_id": 1,  // opcional
        "ttl_minutes": 15  // opcional, default 15
    }
    
    Returns:
    - 200: Stock reservado exitosamente
    - 400: Parámetros inválidos
    - 404: Producto no encontrado
    - 409: Stock insuficiente
    - 500: Error del servidor
    
    Response:
    {
        "success": true,
        "reservation_id": 123,
        "product_sku": "JER-001",
        "quantity_reserved": 2,
        "stock_available": 48,
        "expires_at": "2025-11-14T15:30:00Z",
        "remaining_time_seconds": 900,
        "message": "Stock reservado exitosamente"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        # Validar campos requeridos
        required_fields = ['product_sku', 'quantity', 'user_id', 'session_id']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"{field} is required")
        
        command = ReserveStockCommand(
            product_sku=data['product_sku'],
            quantity=data['quantity'],
            user_id=data['user_id'],
            session_id=data['session_id'],
            distribution_center_id=data.get('distribution_center_id'),
            ttl_minutes=data.get('ttl_minutes', 15)
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
        
    except NotFoundError as e:
        logger.warning(f"⚠️ Not found: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
        
    except ConflictError as e:
        logger.warning(f"⚠️ Conflict: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'INSUFFICIENT_STOCK',
            'message': str(e)
        }), 409
        
    except Exception as e:
        logger.error(f"❌ Error reserving stock: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@cart_bp.route('/release', methods=['POST'])
def release_stock():
    """
    POST /cart/release
    
    Libera stock reservado cuando un usuario remueve productos del carrito.
    
    Body (JSON):
    {
        "product_sku": "JER-001",
        "quantity": 2,
        "user_id": "user123",
        "session_id": "sess-uuid-456"
    }
    
    Returns:
    - 200: Stock liberado exitosamente
    - 400: Parámetros inválidos
    - 500: Error del servidor
    
    Response:
    {
        "success": true,
        "product_sku": "JER-001",
        "quantity_released": 2,
        "stock_available": 50,
        "message": "Stock liberado exitosamente"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        # Validar campos requeridos
        required_fields = ['product_sku', 'quantity', 'user_id', 'session_id']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"{field} is required")
        
        command = ReleaseStockCommand(
            product_sku=data['product_sku'],
            quantity=data['quantity'],
            user_id=data['user_id'],
            session_id=data['session_id']
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Error releasing stock: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@cart_bp.route('/clear', methods=['DELETE', 'POST'])
def clear_cart():
    """
    DELETE /cart/clear
    POST /cart/clear
    
    Limpia todas las reservas de carrito de un usuario.
    
    Body (JSON):
    {
        "user_id": "user123",
        "session_id": "sess-uuid-456"
    }
    
    Returns:
    - 200: Carrito limpiado exitosamente
    - 400: Parámetros inválidos
    - 500: Error del servidor
    
    Response:
    {
        "success": true,
        "cleared_count": 3,
        "products_affected": ["JER-001", "VAC-001", "GUANTE-001"],
        "message": "3 reservas liberadas"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        # Validar campos requeridos
        if 'user_id' not in data or 'session_id' not in data:
            raise ValidationError("user_id and session_id are required")
        
        command = ClearUserCartReservationsCommand(
            user_id=data['user_id'],
            session_id=data['session_id']
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Error clearing cart: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@cart_bp.route('/reservations', methods=['GET'])
def get_user_reservations():
    """
    GET /cart/reservations?user_id=user123&session_id=sess-uuid-456
    
    Obtiene todas las reservas activas de un usuario.
    
    Query Parameters:
    - user_id: ID del usuario (requerido)
    - session_id: ID de sesión (requerido)
    
    Returns:
    - 200: Lista de reservas
    - 400: Parámetros inválidos
    - 500: Error del servidor
    
    Response:
    {
        "success": true,
        "reservations": [
            {
                "id": 1,
                "product_sku": "JER-001",
                "quantity_reserved": 2,
                "expires_at": "2025-11-14T15:30:00Z",
                "remaining_time_seconds": 900,
                "created_at": "2025-11-14T15:15:00Z"
            }
        ],
        "total_count": 1
    }
    """
    try:
        from src.models.cart_reservation import CartReservation
        from sqlalchemy import and_
        from datetime import datetime
        
        user_id = request.args.get('user_id')
        session_id = request.args.get('session_id')
        
        if not user_id or not session_id:
            raise ValidationError("user_id and session_id are required")
        
        # Buscar reservas activas
        reservations = CartReservation.query.filter(
            and_(
                CartReservation.user_id == user_id,
                CartReservation.session_id == session_id,
                CartReservation.is_active == True,
                CartReservation.expires_at > datetime.utcnow()
            )
        ).all()
        
        return jsonify({
            'success': True,
            'reservations': [r.to_dict() for r in reservations],
            'total_count': len(reservations)
        }), 200
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Error getting reservations: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Error interno del servidor'
        }), 500


@cart_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /cart/health
    
    Health check del servicio de carrito.
    """
    return jsonify({
        'status': 'healthy',
        'service': 'cart-reservations',
        'version': '1.0.0'
    }), 200


@cart_bp.route('/stock/realtime', methods=['GET'])
def get_realtime_stock():
    """
    GET /cart/stock/realtime
    
    Obtiene el stock disponible en tiempo real considerando reservas de carrito activas.
    
    Query Parameters:
    - product_sku: SKU del producto (opcional, para consulta de un solo producto)
    - product_skus: Lista de SKUs separados por coma (opcional, para consulta múltiple)
    - distribution_center_id: ID del centro de distribución (opcional)
    
    Response:
    {
        "product_sku": "PROD-001",
        "total_physical_stock": 100,
        "total_reserved_in_carts": 5,
        "total_available_for_purchase": 95,
        "distribution_centers": [
            {
                "distribution_center_id": 1,
                "distribution_center_code": "CDC-BOG-001",
                "distribution_center_name": "Centro Principal Bogotá",
                "city": "Bogotá",
                "physical_stock": 100,
                "reserved_in_carts": 5,
                "available_for_purchase": 95,
                "is_out_of_stock": false
            }
        ]
    }
    """
    try:
        product_sku = request.args.get('product_sku')
        product_skus_str = request.args.get('product_skus')
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        
        product_skus = None
        if product_skus_str:
            product_skus = [sku.strip() for sku in product_skus_str.split(',')]
        
        command = GetRealTimeStock(
            product_sku=product_sku,
            product_skus=product_skus,
            distribution_center_id=distribution_center_id
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error al obtener stock en tiempo real: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': 'Error al obtener stock en tiempo real'
        }), 500

