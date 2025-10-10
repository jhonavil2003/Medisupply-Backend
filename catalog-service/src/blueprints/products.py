from flask import Blueprint, request, jsonify
from src.commands.get_products import GetProducts
from src.commands.get_product_by_sku import GetProductBySKU
from src.errors.errors import ApiError, ValidationError

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('', methods=['GET'])
def list_products():
    """
    GET /products
    
    List products with filtering and pagination
    
    Query Parameters:
    - search: Search in name, description, SKU, barcode, manufacturer
    - sku: Filter by SKU (partial match)
    - category: Filter by category
    - subcategory: Filter by subcategory
    - supplier_id: Filter by supplier ID
    - is_active: Filter by active status (true/false)
    - requires_cold_chain: Filter by cold chain requirement (true/false)
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    
    Returns:
    - 200: List of products with pagination info
    - 400: Invalid parameters
    - 500: Server error
    
    """
    try:
        search = request.args.get('search', type=str)
        sku = request.args.get('sku', type=str)
        category = request.args.get('category', type=str)
        subcategory = request.args.get('subcategory', type=str)
        supplier_id = request.args.get('supplier_id', type=str)
        
        is_active = request.args.get('is_active', type=str)
        if is_active is not None:
            is_active = is_active.lower() in ['true', '1', 'yes']
        
        requires_cold_chain = request.args.get('requires_cold_chain', type=str)
        if requires_cold_chain is not None:
            requires_cold_chain = requires_cold_chain.lower() in ['true', '1', 'yes']
        
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        
        if page < 1:
            raise ValidationError("Page must be greater than 0")
        if per_page < 1 or per_page > 100:
            raise ValidationError("Per page must be between 1 and 100")
        
        command = GetProducts(
            search=search,
            sku=sku,
            category=category,
            subcategory=subcategory,
            supplier_id=supplier_id,
            is_active=is_active,
            requires_cold_chain=requires_cold_chain,
            page=page,
            per_page=per_page
        )
        
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error retrieving products: {str(e)}", status_code=500)


@products_bp.route('/<string:sku>', methods=['GET'])
def get_product_by_sku(sku):
    """
    GET /products/{sku}
    
    Get detailed information about a specific product by SKU
    Includes certifications and regulatory conditions
    
    Path Parameters:
    - sku: Product SKU (required)
    
    Returns:
    - 200: Product details
    - 404: Product not found
    - 500: Server error
    
    Example:
    GET /products/MED-12345
    """
    try:
        command = GetProductBySKU(sku=sku)
        result = command.execute()
        
        return jsonify(result), 200
        
    except ApiError as e:
        raise e
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise ApiError(f"Error retrieving product: {str(e)}", status_code=500)


# Health check endpoint
@products_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /products/health
    
    Health check endpoint
    
    Returns:
    - 200: Service is healthy
    """
    return jsonify({
        'status': 'healthy',
        'service': 'catalog-service',
        'version': '1.0.0'
    }), 200
