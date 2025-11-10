from flask import Blueprint, request, jsonify
from src.commands.get_suppliers import GetSuppliers
from src.commands.get_supplier_by_id import GetSupplierById
from src.commands.create_supplier import CreateSupplier
from src.commands.update_supplier import UpdateSupplier
from src.commands.delete_supplier import DeleteSupplier
from src.errors.errors import ApiError, ValidationError

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')


@suppliers_bp.route('', methods=['GET'])
def list_suppliers():
    """
    GET /suppliers

    List suppliers with optional filters and pagination
    Query params: search, name, country, is_active (true/false), page, per_page
    """
    try:
        search = request.args.get('search', type=str)
        name = request.args.get('name', type=str)
        country = request.args.get('country', type=str)

        is_active_param = request.args.get('is_active', type=str)
        if is_active_param is not None:
            is_active = is_active_param.lower() in ['true', '1', 'yes']
        else:
            is_active = None

        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)

        if page < 1:
            raise ValidationError('Page must be greater than 0')
        if per_page < 1 or per_page > 100:
            raise ValidationError('Per page must be between 1 and 100')

        cmd = GetSuppliers(
            search=search,
            name=name,
            country=country,
            is_active=is_active,
            page=page,
            per_page=per_page
        )

        result = cmd.execute()
        return jsonify(result), 200

    except ValidationError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error retrieving suppliers: {str(e)}", status_code=500)


@suppliers_bp.route('/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    try:
        cmd = GetSupplierById(supplier_id)
        result = cmd.execute()
        return jsonify(result), 200
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error retrieving supplier: {str(e)}", status_code=500)


@suppliers_bp.route('', methods=['POST'])
def create_supplier():
    try:
        try:
            data = request.get_json(force=True)
        except Exception:
            data = None

        if data is None:
            raise ValidationError('Request body is required')

        cmd = CreateSupplier(data)
        result = cmd.execute()
        return jsonify(result), 201
    except ValidationError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error creating supplier: {str(e)}", status_code=500)


@suppliers_bp.route('/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    try:
        try:
            data = request.get_json(force=True)
        except Exception:
            data = None

        if data is None:
            raise ValidationError('Request body is required')

        cmd = UpdateSupplier(supplier_id, data)
        result = cmd.execute()
        return jsonify(result), 200
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error updating supplier: {str(e)}", status_code=500)


@suppliers_bp.route('/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    try:
        cmd = DeleteSupplier(supplier_id)
        result = cmd.execute()
        return jsonify(result), 200
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f"Error deleting supplier: {str(e)}", status_code=500)


# Health check
@suppliers_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'catalog-service', 'module': 'suppliers', 'version': '1.0.0'}), 200
