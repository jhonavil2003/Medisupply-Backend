from flask import Blueprint, request, jsonify
from src.commands.create_order import CreateOrder
from src.commands.get_orders import GetOrders
from src.commands.get_order_by_id import GetOrderById
from src.commands.get_orders_batch import GetOrdersBatch
from src.commands.update_order import UpdateOrder
from src.commands.delete_order import DeleteOrder
from src.errors.errors import NotFoundError, ApiError, ValidationError, ForbiddenError, DatabaseError

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
        delivery_address (str, opcional): Dirección de entrega (default: customer.address)
        delivery_neighborhood (str, opcional): Barrio de entrega (default: customer.neighborhood)
        delivery_city (str, opcional): Ciudad de entrega (default: customer.city)
        delivery_department (str, opcional): Departamento de entrega (default: customer.department)
        delivery_latitude (float, opcional): Latitud GPS de entrega (default: customer.latitude)
        delivery_longitude (float, opcional): Longitud GPS de entrega (default: customer.longitude)
        delivery_date (str, opcional): Fecha estimada de entrega (formato: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
        preferred_distribution_center (str, opcional): Código del centro de distribución preferido
        notes (str, opcional): Notas de la orden
    
    Nota: Los datos del cliente (razón social, documento, teléfono, email) se guardan automáticamente
          como snapshot al momento de crear la orden.
    
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
        delivery_date_from (str, opcional): Fecha de entrega desde (formato: YYYY-MM-DD)
        delivery_date_to (str, opcional): Fecha de entrega hasta (formato: YYYY-MM-DD)
        order_date_from (str, opcional): Fecha de orden desde (formato: YYYY-MM-DD)
        order_date_to (str, opcional): Fecha de orden hasta (formato: YYYY-MM-DD)
    
    Retorna:
        200: Lista de órdenes
        500: Error interno del servidor
    
    Ejemplo:
        GET /orders?customer_id=1&status=pending&delivery_date_from=2025-10-01&delivery_date_to=2025-10-31
    """
    customer_id = request.args.get('customer_id', type=int)
    seller_id = request.args.get('seller_id')
    status = request.args.get('status')
    delivery_date_from = request.args.get('delivery_date_from')
    delivery_date_to = request.args.get('delivery_date_to')
    order_date_from = request.args.get('order_date_from')
    order_date_to = request.args.get('order_date_to')
    
    command = GetOrders(
        customer_id=customer_id,
        seller_id=seller_id,
        status=status,
        delivery_date_from=delivery_date_from,
        delivery_date_to=delivery_date_to,
        order_date_from=order_date_from,
        order_date_to=order_date_to
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


@orders_bp.route('/batch', methods=['POST'])
def get_orders_batch():
    """
    Obtiene múltiples órdenes por sus IDs en una sola operación.
    
    Este endpoint optimiza la comunicación entre microservicios al permitir
    recuperar múltiples órdenes con una sola llamada HTTP, en lugar de
    hacer N llamadas individuales.
    
    Cuerpo de la Petición:
        order_ids (list[int], requerido): Lista de IDs de órdenes a recuperar
    
    Retorna:
        200: Órdenes recuperadas exitosamente
        400: Error de validación (body inválido, order_ids no es lista, etc.)
        500: Error interno del servidor
    
    Ejemplo de Petición:
        POST /orders/batch
        {
            "order_ids": [101, 102, 103, 104]
        }
    
    Ejemplo de Respuesta:
        {
            "orders": [
                {
                    "id": 101,
                    "order_number": "ORD-2025-001",
                    "customer": {
                        "id": 10,
                        "name": "Hospital San Ignacio",
                        "document": "900123456-1",
                        ...
                    },
                    "items": [
                        {
                            "product_sku": "MED-001",
                            "product_name": "Paracetamol 500mg",
                            "quantity": 100,
                            ...
                        }
                    ],
                    "delivery_address": "Calle 100 # 15-20",
                    "delivery_city": "Bogotá",
                    "delivery_department": "Cundinamarca",
                    "delivery_latitude": 4.6825,
                    "delivery_longitude": -74.0543,
                    "clinical_priority": 1,
                    "requires_cold_chain": true,
                    "estimated_weight_kg": 12.5,
                    "estimated_volume_m3": 0.25,
                    "status": "confirmed",
                    ...
                },
                ...
            ],
            "total": 4,
            "not_found": [],
            "requested": 4
        }
    
    Notas:
        - Las órdenes se retornan con detalles completos (include_items=True, include_customer=True)
        - Si algún ID no existe, se incluye en el array 'not_found'
        - Se eliminan IDs duplicados automáticamente
        - El orden de las órdenes retornadas puede no coincidir con el orden de los IDs solicitados
    """
    try:
        # Validar que el request tiene JSON
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json',
                'status_code': 400
            }), 400
        
        data = request.get_json()
        
        # Validar que el body no está vacío
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'status_code': 400
            }), 400
        
        # Validar que order_ids existe y es una lista
        if 'order_ids' not in data:
            return jsonify({
                'error': 'order_ids is required in request body',
                'status_code': 400
            }), 400
        
        order_ids = data['order_ids']
        
        if not isinstance(order_ids, list):
            return jsonify({
                'error': 'order_ids must be an array of integers',
                'status_code': 400
            }), 400
        
        # Validar que todos los elementos son enteros
        if not all(isinstance(order_id, int) for order_id in order_ids):
            return jsonify({
                'error': 'All order_ids must be integers',
                'status_code': 400
            }), 400
        
        # Ejecutar comando
        command = GetOrdersBatch(order_ids)
        result = command.execute()
        
        return jsonify(result), 200
    
    except Exception as e:
        # Error inesperado
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status_code': 500
        }), 500


@orders_bp.route('/<int:order_id>', methods=['PATCH'])
def update_order(order_id):
    """
    Actualiza parcialmente una orden existente (solo órdenes en estado PENDING).
    
    Este endpoint implementa HU-127: Actualización de órdenes con validación de estado.
    Solo permite actualizar órdenes que estén en estado 'pending'.
    Los campos no enviados en el request se mantienen sin cambios (actualización parcial).
    
    Parámetros de Path:
        order_id (int): ID de la orden a actualizar
    
    Cuerpo de la Petición (todos los campos son opcionales):
        status (str, opcional): Nuevo estado ('pending', 'confirmed', 'cancelled')
        payment_method (str, opcional): Método de pago
        payment_terms (str, opcional): Términos de pago (CASH, CREDIT_30, CREDIT_45, etc.)
        delivery_address (str, opcional): Dirección de entrega
        delivery_city (str, opcional): Ciudad de entrega
        delivery_department (str, opcional): Departamento de entrega
        preferred_distribution_center (str, opcional): Código del centro de distribución preferido
        notes (str, opcional): Notas adicionales
        items (list, opcional): Lista completa de items (reemplaza los existentes)
            - product_sku (str, requerido): SKU del producto
            - product_name (str, opcional): Nombre del producto
            - quantity (int, requerido): Cantidad
            - unit_price (float, opcional): Precio unitario
            - discount_percentage (float, opcional): Porcentaje de descuento
            - tax_percentage (float, opcional): Porcentaje de impuesto
            - distribution_center_code (str, opcional): Centro de distribución
            - stock_confirmed (bool, opcional): Stock confirmado
    
    Campos Inmutables (NO pueden modificarse):
        - customer_id
        - seller_id
        - seller_name
        - order_number
        - order_date
        - created_at
        - subtotal, discount_amount, tax_amount, total_amount (auto-calculados)
    
    Retorna:
        200: Orden actualizada exitosamente
        400: Error de validación
            - Orden no está en estado PENDING: "Solo se pueden editar órdenes pendientes"
            - Items vacíos: "Order must have at least one item"
            - Quantity inválida: "Item quantity must be greater than 0"
            - Transición de estado inválida: "Invalid status transition"
            - Formato de datos inválido: "Request body must be a valid JSON object"
        403: Sin permisos para editar la orden
        404: Orden no encontrada
        409: Conflicto (ej: stock insuficiente)
        500: Error interno del servidor
    
    Ejemplo de Petición - Actualizar items:
        PATCH /orders/1
        {
            "items": [
                {
                    "product_sku": "JER-001",
                    "quantity": 15,
                    "discount_percentage": 10.0
                }
            ]
        }
    
    Ejemplo de Petición - Actualizar dirección de entrega:
        PATCH /orders/1
        {
            "delivery_address": "Calle 123 #45-67",
            "delivery_city": "Medellín",
            "delivery_department": "Antioquia"
        }
    
    Ejemplo de Petición - Cambiar estado:
        PATCH /orders/1
        {
            "status": "confirmed"
        }
    
    Errores Comunes:
        - 400: {"error": "Solo se pueden editar órdenes pendientes", "status_code": 400}
        - 400: {"error": "Item at index 0: quantity must be greater than 0", "status_code": 400}
        - 400: {"error": "Invalid status transition: 'pending' → 'cancelled'", "status_code": 400}
        - 404: {"error": "Order with id 999 not found", "status_code": 404}
        - 500: {"error": "Database error while updating order", "status_code": 500}
    """
    try:
        # Validate request has JSON body
        if not request.is_json:
            return jsonify({
                'error': 'Content-Type must be application/json',
                'status_code': 400
            }), 400
        
        data = request.get_json()
        
        # Validate request body is not empty
        if not data or not isinstance(data, dict):
            return jsonify({
                'error': 'Request body is required and must be a valid JSON object',
                'status_code': 400
            }), 400
        
        # Validate at least one field is being updated
        if len(data) == 0:
            return jsonify({
                'error': 'Request body cannot be empty. At least one field must be provided for update',
                'status_code': 400
            }), 400
        
        # TODO: Implementar validación de permisos (por ahora asumimos que tiene permisos)
        # Example implementation:
        # user_id = request.headers.get('X-User-Id')  # or from JWT token
        # if not user_has_permission_to_edit(order_id, user_id):
        #     raise ForbiddenError('No tiene permisos para editar esta orden')
        
        # Execute update command
        command = UpdateOrder(order_id, data)
        updated_order = command.execute()
        
        return jsonify(updated_order), 200
    
    except NotFoundError as e:
        # 404 - Order not found
        return jsonify({
            'error': str(e),
            'status_code': 404,
            'order_id': order_id
        }), 404
    
    except ValidationError as e:
        # 400 - Validation error (format, required fields, invalid values)
        return jsonify({
            'error': str(e),
            'status_code': 400
        }), 400
    
    except ApiError as e:
        # 400/409 - Business rule violation (status not PENDING, invalid transition, etc.)
        return jsonify({
            'error': str(e),
            'status_code': e.status_code
        }), e.status_code
    
    except ForbiddenError as e:
        # 403 - Permission denied
        return jsonify({
            'error': str(e),
            'status_code': 403
        }), 403
    
    except DatabaseError as e:
        # 500 - Database error
        return jsonify({
            'error': str(e),
            'status_code': 500
        }), 500
    
    except Exception as e:
        # 500 - Unexpected error
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status_code': 500
        }), 500


@orders_bp.route('/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    """
    Elimina una orden por ID (solo órdenes en estado PENDING).
    
    Solo permite eliminar órdenes que estén en estado 'pending'.
    Órdenes confirmadas, en proceso o entregadas no pueden ser eliminadas.
    
    Parámetros de Path:
        order_id (int): ID de la orden a eliminar
    
    Retorna:
        200: Orden eliminada exitosamente
        400: Orden no está en estado PENDING
        404: Orden no encontrada
    
    Ejemplo:
        DELETE /orders/1
    
    Errores Comunes:
        - 400: {"error": "Solo se pueden eliminar órdenes en estado 'pending'. Esta orden está en estado 'confirmed'", "status_code": 400}
        - 404: {"error": "Order with ID 999 not found", "status_code": 404}
    """
    try:
        command = DeleteOrder(order_id)
        result = command.execute()
        
        return jsonify(result), 200
    
    except NotFoundError as e:
        # 404 - Order not found
        return jsonify({
            'error': str(e),
            'status_code': 404
        }), 404
    
    except ApiError as e:
        # 400 - Order is not in PENDING status
        return jsonify({
            'error': str(e),
            'status_code': e.status_code
        }), e.status_code
    
    except Exception as e:
        # 500 - Unexpected error
        return jsonify({
            'error': f'Internal server error: {str(e)}',
            'status_code': 500
        }), 500


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
