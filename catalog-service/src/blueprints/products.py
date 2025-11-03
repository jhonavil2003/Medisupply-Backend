from flask import Blueprint, request, jsonify
from src.commands.get_products import GetProducts
from src.commands.get_product_by_id import GetProductById
from src.commands.get_product_by_sku import GetProductBySKU
from src.commands.create_product import CreateProduct
from src.commands.update_product import UpdateProduct
from src.commands.delete_product import DeleteProduct
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
        
        is_active_param = request.args.get('is_active', type=str)
        if is_active_param is not None:
            is_active = is_active_param.lower() in ['true', '1', 'yes']
        else:
            is_active = True
        
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


@products_bp.route('', methods=['POST'])
def create_product():
    """
    POST /products
    
    Create a new product
    
    Request Body:
    {
        "sku": "string (required)",
        "name": "string (required)",
        "description": "string (optional)",
        "category": "string (required)",
        "subcategory": "string (optional)",
        "unit_price": "number (required)",
        "currency": "string (optional, default: USD)",
        "unit_of_measure": "string (required)",
        "supplier_id": "integer (required)",
        "requires_cold_chain": "boolean (optional, default: false)",
        "storage_temperature_min": "number (optional)",
        "storage_temperature_max": "number (optional)",
        "storage_humidity_max": "number (optional)",
        "sanitary_registration": "string (optional)",
        "requires_prescription": "boolean (optional, default: false)",
        "regulatory_class": "string (optional)",
        "weight_kg": "number (optional)",
        "length_cm": "number (optional)",
        "width_cm": "number (optional)",
        "height_cm": "number (optional)",
        "manufacturer": "string (optional)",
        "country_of_origin": "string (optional)",
        "barcode": "string (optional)",
        "image_url": "string (optional)"
    }
    
    Returns:
    - 201: Product created successfully
    - 400: Validation error
    - 500: Server error
    """
    try:
        try:
            data = request.get_json(force=True)
        except Exception:
            # If JSON parsing fails, treat as missing request body
            data = None
        
        if data is None:
            raise ValidationError("Request body is required")
        
        if not isinstance(data, dict):
            raise ValidationError("Request body must be a JSON object")
        
        command = CreateProduct(data)
        result = command.execute()
        
        return jsonify(result), 201
        
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error creating product: {str(e)}", status_code=500)


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product_by_id(product_id):
    """
    GET /products/{product_id}
    
    Get detailed information about a specific product by ID
    Includes certifications and regulatory conditions
    
    Path Parameters:
    - product_id: Product ID (required)
    
    Returns:
    - 200: Product details
    - 404: Product not found
    - 500: Server error
    
    Example:
    GET /products/12
    """
    try:
        command = GetProductById(product_id=product_id)
        result = command.execute()
        
        return jsonify(result), 200
        
    except ApiError as e:
        raise e
    except ValueError as e:
        raise ValidationError(str(e))
    except Exception as e:
        raise ApiError(f"Error retrieving product: {str(e)}", status_code=500)


@products_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    PUT /products/{product_id}
    
    Update an existing product
    
    Path Parameters:
    - product_id: Product ID (required)
    
    Request Body: Same as POST but all fields are optional
    
    Returns:
    - 200: Product updated successfully
    - 400: Validation error
    - 404: Product not found
    - 500: Server error
    """
    try:
        try:
            data = request.get_json(force=True)
        except Exception:
            # If JSON parsing fails, treat as missing request body
            data = None
        
        if data is None:
            raise ValidationError("Request body is required")
        
        if not isinstance(data, dict):
            raise ValidationError("Request body must be a JSON object")
        
        command = UpdateProduct(product_id, data)
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        raise e
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error updating product: {str(e)}", status_code=500)


@products_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    DELETE /products/{product_id}
    
    Delete (deactivate) a product
    
    Path Parameters:
    - product_id: Product ID (required)
    
    Query Parameters:
    - hard_delete: true/false (optional, default: false)
      If true, permanently removes the product from database
      If false, performs soft delete (sets is_active=false)
    
    Returns:
    - 200: Product deleted successfully
    - 404: Product not found
    - 500: Server error
    """
    try:
        hard_delete = request.args.get('hard_delete', 'false').lower() == 'true'
        
        command = DeleteProduct(product_id)
        
        if hard_delete:
            result = command.execute_hard_delete()
        else:
            result = command.execute()
        
        return jsonify(result), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error deleting product: {str(e)}", status_code=500)


@products_bp.route('/<string:sku>', methods=['GET'])
def get_product_by_sku(sku):
    """
    GET /products/<sku>
    
    Get a product by SKU
    
    Args:
    - sku: Product SKU
    
    Returns:
    - 200: Product details
    - 404: Product not found
    - 500: Server error
    """
    try:
        command = GetProductBySKU(sku)
        result = command.execute()
        return jsonify(result), 200
    except ApiError as e:
        raise e
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
