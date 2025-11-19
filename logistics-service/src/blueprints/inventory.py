from flask import Blueprint, request, jsonify
from src.commands.get_stock_levels import GetStockLevels
from src.commands.get_product_location import GetProductLocation
from src.errors.errors import ApiError, ValidationError, NotFoundError
from src.models.inventory import Inventory
from src.session import db
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/stock-levels', methods=['GET'])
def get_stock_levels():
    """
    GET /inventory/stock-levels
    
    Consulta niveles de stock en tiempo real por producto y centro de distribución
    
    Query Parameters:
    - product_sku: SKU del producto (opcional, para consulta de un solo producto)
    - product_skus: Lista de SKUs separados por coma (opcional, para consulta múltiple)
    - distribution_center_id: ID del centro de distribución (opcional)
    - only_available: Filtrar solo productos con stock disponible (true/false, default: false)
    - include_reserved: Incluir cantidades reservadas (true/false, default: true)
    - include_in_transit: Incluir cantidades en tránsito (true/false, default: false)
    
    Returns:
    - 200: Niveles de stock encontrados
    - 400: Parámetros inválidos
    - 500: Error del servidor
    
    Examples:
    - GET /inventory/stock-levels?product_sku=JER-001
    - GET /inventory/stock-levels?product_skus=JER-001,VAC-001,GUANTE-001
    - GET /inventory/stock-levels?product_sku=JER-001&distribution_center_id=1
    """
    try:
        product_sku = request.args.get('product_sku', type=str)
        product_skus_param = request.args.get('product_skus', type=str)
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        
        product_skus = []
        if product_skus_param:
            product_skus = [sku.strip() for sku in product_skus_param.split(',') if sku.strip()]
        
        only_available = request.args.get('only_available', 'false').lower() in ['true', '1', 'yes']
        include_reserved = request.args.get('include_reserved', 'true').lower() in ['true', '1', 'yes']
        include_in_transit = request.args.get('include_in_transit', 'false').lower() in ['true', '1', 'yes']
        
        if not product_sku and not product_skus:
            raise ValidationError("Se requiere al menos product_sku o product_skus")
        
        if product_sku and product_skus:
            raise ValidationError("No se puede usar product_sku y product_skus simultáneamente")
        
        command = GetStockLevels(
            product_sku=product_sku,
            product_skus=product_skus,
            distribution_center_id=distribution_center_id,
            only_available=only_available,
            include_reserved=include_reserved,
            include_in_transit=include_in_transit
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error retrieving stock levels: {str(e)}", status_code=500)


@inventory_bp.route('/product-location', methods=['GET'])
def get_product_location():
    """
    GET /inventory/product-location
    
    Consulta la localización de un producto en bodega, incluyendo lote, fecha de vencimiento
    y condiciones de temperatura. Los resultados se ordenan por FEFO (First-Expire-First-Out)
    por defecto.
    
    Query Parameters:
    - search_term: Término de búsqueda general (busca en SKU, barcode, QR, código interno)
    - product_sku: SKU del producto (búsqueda específica)
    - barcode: Código de barras del lote
    - qr_code: Código QR del lote
    - internal_code: Código interno de la organización
    - distribution_center_id: ID del centro de distribución (opcional)
    - batch_number: Número de lote específico (opcional)
    - zone_type: Tipo de zona ('refrigerated' o 'ambient')
    - expiry_date_from: Fecha de vencimiento desde (formato YYYY-MM-DD)
    - expiry_date_to: Fecha de vencimiento hasta (formato YYYY-MM-DD)
    - include_expired: Incluir lotes vencidos (true/false, default: false)
    - include_quarantine: Incluir lotes en cuarentena (true/false, default: false)
    - only_available: Solo lotes disponibles (true/false, default: true)
    - order_by: Criterio de ordenamiento ('fefo', 'quantity', 'location', default: 'fefo')
    
    Returns:
    - 200: Localización encontrada con detalles completos
    - 400: Parámetros inválidos
    - 404: Producto no encontrado
    - 500: Error del servidor
    
    Examples:
    - GET /inventory/product-location?product_sku=JER-001
    - GET /inventory/product-location?barcode=7501234567890
    - GET /inventory/product-location?search_term=GUANTE&zone_type=refrigerated
    - GET /inventory/product-location?product_sku=VAC-001&expiry_date_from=2025-01-01&expiry_date_to=2025-12-31
    """
    try:
        # Parámetros de búsqueda principales
        search_term = request.args.get('search_term', type=str)
        product_sku = request.args.get('product_sku', type=str)
        barcode = request.args.get('barcode', type=str)
        qr_code = request.args.get('qr_code', type=str)
        internal_code = request.args.get('internal_code', type=str)
        
        # Filtros adicionales
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        batch_number = request.args.get('batch_number', type=str)
        zone_type = request.args.get('zone_type', type=str)
        expiry_date_from = request.args.get('expiry_date_from', type=str)
        expiry_date_to = request.args.get('expiry_date_to', type=str)
        
        # Opciones de filtrado
        include_expired = request.args.get('include_expired', 'false').lower() in ['true', '1', 'yes']
        include_quarantine = request.args.get('include_quarantine', 'false').lower() in ['true', '1', 'yes']
        only_available = request.args.get('only_available', 'true').lower() in ['true', '1', 'yes']
        
        # Ordenamiento
        order_by = request.args.get('order_by', 'fefo', type=str)
        
        # Validar que se proporcione al menos un parámetro de búsqueda
        if not any([search_term, product_sku, barcode, qr_code, internal_code]):
            raise ValidationError(
                "Se requiere al menos un parámetro de búsqueda: "
                "search_term, product_sku, barcode, qr_code o internal_code"
            )
        
        # Crear y ejecutar comando
        command = GetProductLocation(
            search_term=search_term,
            product_sku=product_sku,
            barcode=barcode,
            qr_code=qr_code,
            internal_code=internal_code,
            distribution_center_id=distribution_center_id,
            batch_number=batch_number,
            zone_type=zone_type,
            expiry_date_from=expiry_date_from,
            expiry_date_to=expiry_date_to,
            include_expired=include_expired,
            include_quarantine=include_quarantine,
            only_available=only_available,
            order_by=order_by
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        raise e
    except NotFoundError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error retrieving product location: {str(e)}", status_code=500)


@inventory_bp.route('', methods=['POST'])
def create_inventory():
    """
    POST /inventory
    
    Crea un nuevo registro de inventario para un producto en un centro de distribución.
    
    Body (JSON):
    {
        "product_sku": "JER-001",
        "distribution_center_id": 1,
        "quantity_available": 500,
        "quantity_reserved": 0,
        "quantity_in_transit": 0,
        "minimum_stock_level": 50,
        "maximum_stock_level": 1000,
        "reorder_point": 150,
        "unit_cost": 10.50
    }
    
    Returns:
    - 201: Inventario creado exitosamente
    - 400: Datos inválidos
    - 409: Ya existe inventario para este producto en este centro
    - 500: Error del servidor
    """
    from src.session import db
    from src.models.inventory import Inventory
    from src.models.distribution_center import DistributionCenter
    from datetime import datetime
    
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        # Validar campos requeridos
        product_sku = data.get('product_sku')
        distribution_center_id = data.get('distribution_center_id')
        
        if not product_sku:
            raise ValidationError("product_sku is required")
        
        if not distribution_center_id:
            raise ValidationError("distribution_center_id is required")
        
        # Verificar que el centro de distribución existe
        distribution_center = DistributionCenter.query.get(distribution_center_id)
        if not distribution_center:
            raise NotFoundError(f"Distribution center with id {distribution_center_id} not found")
        
        # Verificar que no existe ya un inventario para este producto en este centro
        existing = Inventory.query.filter_by(
            product_sku=product_sku.upper(),
            distribution_center_id=distribution_center_id
        ).first()
        
        if existing:
            raise ValidationError(
                f"Inventory already exists for product {product_sku} in distribution center {distribution_center_id}"
            )
        
        # Crear nuevo inventario
        inventory = Inventory(
            product_sku=product_sku.upper(),
            distribution_center_id=distribution_center_id,
            quantity_available=data.get('quantity_available', 0),
            quantity_reserved=data.get('quantity_reserved', 0),
            quantity_in_transit=data.get('quantity_in_transit', 0),
            minimum_stock_level=data.get('minimum_stock_level', 0),
            maximum_stock_level=data.get('maximum_stock_level'),
            reorder_point=data.get('reorder_point'),
            unit_cost=data.get('unit_cost'),
            last_restock_date=datetime.utcnow() if data.get('quantity_available', 0) > 0 else None,
            last_movement_date=datetime.utcnow()
        )
        
        db.session.add(inventory)
        db.session.commit()
        
        return jsonify(inventory.to_dict(include_center=True)), 201
        
    except ValidationError as e:
        raise e
    except NotFoundError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise ApiError(f"Error creating inventory: {str(e)}", status_code=500)


@inventory_bp.route('/<product_sku>/update', methods=['PUT', 'PATCH'])
def update_inventory(product_sku):
    """
    PUT/PATCH /inventory/<product_sku>/update
    
    Actualiza uno o varios campos del inventario de un producto.
    Esta actualización dispara automáticamente una notificación WebSocket 
    cuando se modifica quantity_available.
    
    Path Parameters:
    - product_sku: SKU del producto a actualizar
    
    Body Parameters (todos opcionales, pero al menos uno requerido):
    - distribution_center_id: ID del centro de distribución (requerido si el producto existe en múltiples centros)
    - quantity_available: Nueva cantidad disponible
    - quantity_reserved: Nueva cantidad reservada
    - quantity_in_transit: Nueva cantidad en tránsito
    - minimum_stock_level: Nivel mínimo de stock
    - maximum_stock_level: Nivel máximo de stock
    - reorder_point: Punto de reorden
    - unit_cost: Costo unitario
    - trigger_websocket: Si false, no dispara notificación WebSocket (default: true)
    
    Returns:
    - 200: Inventario actualizado exitosamente
    - 400: Parámetros inválidos
    - 404: Producto no encontrado en inventario
    - 500: Error del servidor
    
    Examples:
    
    1. Actualizar solo cantidad disponible:
    PUT /inventory/JER-001/update
    {
        "distribution_center_id": 1,
        "quantity_available": 75
    }
    
    2. Actualizar múltiples campos:
    PUT /inventory/JER-001/update
    {
        "distribution_center_id": 1,
        "quantity_available": 100,
        "quantity_reserved": 20,
        "minimum_stock_level": 50,
        "unit_cost": 15.50
    }
    
    3. Actualizar sin disparar WebSocket:
    PUT /inventory/JER-001/update
    {
        "distribution_center_id": 1,
        "quantity_available": 150,
        "trigger_websocket": false
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Se requiere el body de la petición")
        
        distribution_center_id = data.get('distribution_center_id')
        
        # Campos actualizables
        quantity_available = data.get('quantity_available')
        quantity_reserved = data.get('quantity_reserved')
        quantity_in_transit = data.get('quantity_in_transit')
        minimum_stock_level = data.get('minimum_stock_level')
        maximum_stock_level = data.get('maximum_stock_level')
        reorder_point = data.get('reorder_point')
        unit_cost = data.get('unit_cost')
        trigger_websocket = data.get('trigger_websocket', True)
        
        # Validar que al menos un campo esté presente
        updatable_fields = [
            quantity_available, quantity_reserved, quantity_in_transit,
            minimum_stock_level, maximum_stock_level, reorder_point, unit_cost
        ]
        if all(field is None for field in updatable_fields):
            raise ValidationError(
                "Se requiere al menos uno de los siguientes campos: "
                "quantity_available, quantity_reserved, quantity_in_transit, "
                "minimum_stock_level, maximum_stock_level, reorder_point, unit_cost"
            )
        
        # Buscar el inventario
        query = db.session.query(Inventory).filter_by(product_sku=product_sku)
        
        if distribution_center_id:
            query = query.filter_by(distribution_center_id=distribution_center_id)
        else:
            # Si no se especifica centro de distribución, verificar que solo exista uno
            all_inventory = db.session.query(Inventory).filter_by(product_sku=product_sku).all()
            if len(all_inventory) > 1:
                raise ValidationError(
                    f"El producto '{product_sku}' existe en {len(all_inventory)} centros de distribución. "
                    "Por favor especifica 'distribution_center_id'"
                )
        
        inventory = query.first()
        
        if not inventory:
            raise NotFoundError(
                f"No se encontró inventario para el producto '{product_sku}'"
                + (f" en el centro de distribución {distribution_center_id}" if distribution_center_id else "")
            )
        
        # Guardar valores anteriores para el response
        changes = {}
        old_quantity_available = inventory.quantity_available
        
        # Actualizar campos
        if quantity_available is not None:
            if not isinstance(quantity_available, (int, float)) or quantity_available < 0:
                raise ValidationError("'quantity_available' debe ser un número no negativo")
            
            if trigger_websocket:
                # Usar el método que dispara WebSocket
                inventory.update_quantity_available(quantity_available, auto_notify=True)
            else:
                # Actualizar sin disparar WebSocket
                inventory.quantity_available = quantity_available
                inventory.last_movement_date = datetime.utcnow()
            
            changes['quantity_available'] = {
                'old': old_quantity_available,
                'new': inventory.quantity_available
            }
        
        if quantity_reserved is not None:
            if not isinstance(quantity_reserved, (int, float)) or quantity_reserved < 0:
                raise ValidationError("'quantity_reserved' debe ser un número no negativo")
            changes['quantity_reserved'] = {
                'old': inventory.quantity_reserved,
                'new': quantity_reserved
            }
            inventory.quantity_reserved = quantity_reserved
        
        if quantity_in_transit is not None:
            if not isinstance(quantity_in_transit, (int, float)) or quantity_in_transit < 0:
                raise ValidationError("'quantity_in_transit' debe ser un número no negativo")
            changes['quantity_in_transit'] = {
                'old': inventory.quantity_in_transit,
                'new': quantity_in_transit
            }
            inventory.quantity_in_transit = quantity_in_transit
        
        if minimum_stock_level is not None:
            if not isinstance(minimum_stock_level, (int, float)) or minimum_stock_level < 0:
                raise ValidationError("'minimum_stock_level' debe ser un número no negativo")
            changes['minimum_stock_level'] = {
                'old': inventory.minimum_stock_level,
                'new': minimum_stock_level
            }
            inventory.minimum_stock_level = minimum_stock_level
        
        if maximum_stock_level is not None:
            if not isinstance(maximum_stock_level, (int, float)) or maximum_stock_level < 0:
                raise ValidationError("'maximum_stock_level' debe ser un número no negativo")
            changes['maximum_stock_level'] = {
                'old': inventory.maximum_stock_level,
                'new': maximum_stock_level
            }
            inventory.maximum_stock_level = maximum_stock_level
        
        if reorder_point is not None:
            if not isinstance(reorder_point, (int, float)) or reorder_point < 0:
                raise ValidationError("'reorder_point' debe ser un número no negativo")
            changes['reorder_point'] = {
                'old': inventory.reorder_point,
                'new': reorder_point
            }
            inventory.reorder_point = reorder_point
        
        if unit_cost is not None:
            if not isinstance(unit_cost, (int, float)) or unit_cost < 0:
                raise ValidationError("'unit_cost' debe ser un número no negativo")
            changes['unit_cost'] = {
                'old': float(inventory.unit_cost) if inventory.unit_cost else None,
                'new': unit_cost
            }
            inventory.unit_cost = unit_cost
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Inventario actualizado para {product_sku}',
            'data': {
                'product_sku': product_sku,
                'distribution_center_id': inventory.distribution_center_id,
                'distribution_center': inventory.distribution_center.to_dict() if inventory.distribution_center else None,
                'changes': changes,
                'current_state': inventory.to_dict(include_center=False),
                'websocket_notification_sent': trigger_websocket and quantity_available is not None
            }
        }), 200
        
    except ValidationError as e:
        db.session.rollback()
        raise e
    except NotFoundError as e:
        db.session.rollback()
        raise e
    except Exception as e:
        db.session.rollback()
        raise ApiError(f"Error al procesar la solicitud: {str(e)}", status_code=500)


@inventory_bp.route('/reserve-for-order', methods=['POST'])
def reserve_for_order():
    """
    POST /inventory/reserve-for-order
    
    Reserva inventario para una orden confirmada.
    Actualiza quantity_reserved en la tabla inventory para todos los items de la orden.
    
    Este endpoint debe ser llamado inmediatamente después de crear una orden
    para asegurar que el inventario refleja las cantidades comprometidas.
    
    Body (JSON):
    {
        "order_id": "ORD-2025-001",
        "items": [
            {
                "product_sku": "JER-001",
                "quantity": 5,
                "distribution_center_id": 1
            },
            {
                "product_sku": "MED-002",
                "quantity": 10,
                "distribution_center_id": 1
            }
        ]
    }
    
    Returns:
    - 200: Inventario reservado exitosamente
    - 400: Parámetros inválidos
    - 404: Producto no encontrado en inventario
    - 409: Stock insuficiente
    - 500: Error del servidor
    
    Response:
    {
        "success": true,
        "order_id": "ORD-2025-001",
        "items_reserved": [
            {
                "product_sku": "JER-001",
                "quantity_reserved": 5,
                "distribution_center_id": 1,
                "quantity_reserved_before": 100,
                "quantity_reserved_after": 105,
                "quantity_available": 495
            },
            ...
        ],
        "message": "Inventario reservado exitosamente para 2 items"
    }
    """
    from src.commands.reserve_inventory_for_order import ReserveInventoryForOrder
    
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        # Validar campos requeridos
        if 'order_id' not in data:
            raise ValidationError("order_id is required")
        
        if 'items' not in data:
            raise ValidationError("items is required")
        
        # Ejecutar comando
        command = ReserveInventoryForOrder(
            order_id=data['order_id'],
            items=data['items']
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
        
    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


@inventory_bp.route('/release-for-order', methods=['POST'])
def release_for_order():
    """
    POST /inventory/release-for-order
    
    Libera inventario reservado cuando se cancela una orden.
    Reduce quantity_reserved en la tabla inventory para todos los items.
    
    Body (JSON):
    {
        "order_id": "ORD-2025-001",
        "items": [
            {
                "product_sku": "JER-001",
                "quantity": 5,
                "distribution_center_id": 1
            },
            ...
        ]
    }
    
    Returns:
    - 200: Inventario liberado exitosamente
    - 400: Parámetros inválidos
    - 404: Producto no encontrado
    - 500: Error del servidor
    """
    from src.commands.reserve_inventory_for_order import ReleaseInventoryForOrder
    
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("Request body is required")
        
        if 'order_id' not in data:
            raise ValidationError("order_id is required")
        
        if 'items' not in data:
            raise ValidationError("items is required")
        
        command = ReleaseInventoryForOrder(
            order_id=data['order_id'],
            items=data['items']
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'VALIDATION_ERROR',
            'message': str(e)
        }), 400
        
    except NotFoundError as e:
        return jsonify({
            'success': False,
            'error': 'NOT_FOUND',
            'message': str(e)
        }), 404
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'SERVER_ERROR',
            'message': str(e)
        }), 500


# Health check endpoint
@inventory_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /inventory/health
    
    Health check endpoint
    
    Returns:
    - 200: Service is healthy
    """
    return jsonify({
        'status': 'healthy',
        'service': 'logistics-service',
        'version': '1.0.0'
    }), 200
