from flask import Blueprint, request, jsonify
from src.commands.get_stock_levels import GetStockLevels
from src.commands.get_product_location import GetProductLocation
from src.errors.errors import ApiError, ValidationError, NotFoundError

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
