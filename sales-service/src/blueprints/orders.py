from flask import Blueprint, request, jsonify
from src.commands.create_order import CreateOrder
from src.commands.get_orders import GetOrders
from src.commands.get_order_by_id import GetOrderById
from src.commands.delete_order import DeleteOrder

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')


@orders_bp.route('', methods=['POST'])
def create_order():
    """
    Crea una nueva orden con validación de stock en tiempo real.
    
    Este endpoint implementa HU-102: Crear orden desde app móvil con verificación de disponibilidad en tiempo real.
    
    Cuerpo de la Petición:
        customer_id (int, requerido): ID del cliente
        seller_id (str, requerido): ID del vendedor
        seller_name (str, opcional): Nombre del vendedor
        items (list, requerido): Lista de ítems de la orden
            - product_sku (str, requerido): SKU del producto
            - quantity (int, requerido): Cantidad
            - discount_percentage (float, opcional): Porcentaje de descuento (default: 0.0)
            - tax_percentage (float, opcional): Porcentaje de impuestos (default: 19.0)
        payment_terms (str, opcional): Términos de pago (default: 'contado')
        payment_method (str, opcional): Método de pago
        delivery_address (str, opcional): Dirección de entrega
        delivery_city (str, opcional): Ciudad de entrega
        delivery_department (str, opcional): Departamento de entrega
        preferred_distribution_center (str, opcional): Código del centro de distribución preferido
        notes (str, opcional): Notas de la orden
    
    Retorna:
        201: Orden creada exitosamente
        400: Error de validación
        404: Cliente o producto no encontrado
        409: Stock insuficiente
        503: Servicio externo no disponible
    
    Ejemplo de Petición:
        POST /orders
        {
            "customer_id": 1,
            "seller_id": "SELLER-001",
            "seller_name": "Juan Pérez",
            "items": [
                {
                    "product_sku": "JER-001",
                    "quantity": 10,
                    "discount_percentage": 5.0
                },
                {
                    "product_sku": "VAC-001",
                    "quantity": 5
                }
            ],
            "payment_terms": "credito_30",
            "payment_method": "transferencia",
            "preferred_distribution_center": "DC-BOG-001",
            "notes": "Entrega urgente"
        }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({
            'error': 'Request body is required',
            'status_code': 400
        }), 400
    
    command = CreateOrder(data)
    order = command.execute()
    
    return jsonify(order), 201


@orders_bp.route('', methods=['GET'])
def get_orders():
    """
    Obtiene la lista de órdenes con filtrado opcional.
    
    Parámetros de Query:
        customer_id (int, opcional): Filtrar por ID del cliente
        seller_id (str, opcional): Filtrar por ID del vendedor
        status (str, opcional): Filtrar por estado
    
    Retorna:
        200: Lista de órdenes
        500: Error interno del servidor
    
    Ejemplo:
        GET /orders?customer_id=1&status=pending
    """
    customer_id = request.args.get('customer_id', type=int)
    seller_id = request.args.get('seller_id')
    status = request.args.get('status')
    
    command = GetOrders(
        customer_id=customer_id,
        seller_id=seller_id,
        status=status
    )
    
    orders = command.execute()
    
    return jsonify({
        'orders': orders,
        'total': len(orders)
    }), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """
    Obtiene una orden por ID con todos los detalles.
    
    Parámetros de Path:
        order_id (int): ID de la orden
    
    Retorna:
        200: Detalles de la orden con ítems y cliente
        404: Orden no encontrada
    
    Ejemplo:
        GET /orders/1
    """
    command = GetOrderById(order_id)
    order = command.execute()
    
    return jsonify(order), 200


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Elimina una orden por ID.
    
    Parámetros de Path:
        order_id (int): ID de la orden a eliminar
    
    Retorna:
        200: Orden eliminada exitosamente
        404: Orden no encontrada
    
    Ejemplo:
        DELETE /orders/1
    """
    command = DeleteOrder(order_id)
    result = command.execute()
    
    return jsonify(result), 200


@orders_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de health check para el servicio de órdenes.
    
    Retorna:
        200: El servicio está saludable
    """
    return jsonify({
        'service': 'sales-service',
        'module': 'orders',
        'status': 'healthy',
        'version': '1.0.0'
    }), 200
