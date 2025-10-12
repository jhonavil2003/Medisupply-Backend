from flask import Blueprint, request, jsonify
from src.commands.get_stock_levels import GetStockLevels
from src.errors.errors import ApiError, ValidationError

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
