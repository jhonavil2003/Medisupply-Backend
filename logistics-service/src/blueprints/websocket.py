"""
Blueprint para endpoints WebSocket de prueba y monitoreo.
"""

from flask import Blueprint, jsonify
from src.websockets.websocket_manager import socketio, InventoryNotifier

websocket_bp = Blueprint('websocket', __name__, url_prefix='/websocket')


@websocket_bp.route('/health', methods=['GET'])
def websocket_health():
    """
    GET /websocket/health
    
    Endpoint de health check para verificar que el servidor WebSocket está activo.
    
    Returns:
    - 200: WebSocket server is healthy
    """
    return jsonify({
        'status': 'healthy',
        'message': 'WebSocket server is running',
        'endpoint': '/socket.io/',
        'protocols': ['websocket', 'polling']
    }), 200


@websocket_bp.route('/test-notification', methods=['POST'])
def test_notification():
    """
    POST /websocket/test-notification
    
    Endpoint de prueba para enviar notificación de test.
    Útil para verificar que las notificaciones funcionan correctamente.
    
    Body:
    {
        "product_sku": "JER-001",
        "change_type": "update"  // opcional
    }
    
    Returns:
    - 200: Notification sent
    - 400: Invalid request
    """
    from flask import request
    
    data = request.get_json()
    
    if not data or 'product_sku' not in data:
        return jsonify({
            'error': 'product_sku is required'
        }), 400
    
    product_sku = data['product_sku']
    change_type = data.get('change_type', 'update')
    
    # Enviar notificación de prueba
    test_stock_data = {
        'product_sku': product_sku,
        'total_available': 100,
        'total_reserved': 10,
        'total_in_transit': 5,
        'distribution_centers': [
            {
                'distribution_center_id': 1,
                'distribution_center_code': 'CEDIS-BOG',
                'quantity_available': 100
            }
        ],
        'test': True
    }
    
    InventoryNotifier.notify_stock_change(
        product_sku=product_sku,
        stock_data=test_stock_data,
        change_type=change_type
    )
    
    return jsonify({
        'status': 'success',
        'message': f'Test notification sent for {product_sku}',
        'change_type': change_type
    }), 200


@websocket_bp.route('/info', methods=['GET'])
def websocket_info():
    """
    GET /websocket/info
    
    Información sobre cómo conectarse al WebSocket.
    
    Returns:
    - 200: Connection information
    """
    return jsonify({
        'websocket_url': 'http://localhost:3002',
        'socket_path': '/socket.io/',
        'events': {
            'client_events': {
                'connect': 'Conectar al servidor',
                'disconnect': 'Desconectar del servidor',
                'subscribe_products': 'Suscribirse a productos específicos (enviar: {product_skus: []})',
                'unsubscribe_products': 'Desuscribirse de productos',
                'subscribe_all_products': 'Suscribirse a todos los productos',
                'ping': 'Ping para mantener conexión'
            },
            'server_events': {
                'connection_established': 'Confirmación de conexión exitosa',
                'stock_updated': 'Notificación de cambio de stock',
                'subscribed': 'Confirmación de suscripción a productos',
                'subscribed_all': 'Confirmación de suscripción global',
                'unsubscribed': 'Confirmación de desuscripción',
                'pong': 'Respuesta a ping',
                'error': 'Error en operación'
            }
        },
        'payload_examples': {
            'subscribe_products': {
                'product_skus': ['JER-001', 'VAC-001', 'GUANTE-001']
            },
            'stock_updated': {
                'product_sku': 'JER-001',
                'change_type': 'update',
                'timestamp': '2025-10-30T14:30:00Z',
                'stock_data': {
                    'product_sku': 'JER-001',
                    'total_available': 450,
                    'total_reserved': 50,
                    'total_in_transit': 0,
                    'distribution_centers': [
                        {
                            'distribution_center_id': 1,
                            'distribution_center_code': 'CEDIS-BOG',
                            'quantity_available': 300
                        }
                    ],
                    'quantity_change': -50,
                    'previous_quantity': 500,
                    'new_quantity': 450
                }
            }
        },
        'libraries': {
            'kotlin': 'implementation("io.socket:socket.io-client:2.1.0")',
            'javascript': 'npm install socket.io-client',
            'python': 'pip install python-socketio[client]'
        }
    }), 200
