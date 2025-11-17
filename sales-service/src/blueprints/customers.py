from flask import Blueprint, request, jsonify
from src.commands.get_customers import GetCustomers
from src.commands.get_customer_by_id import GetCustomerById
from src.commands.create_customer import CreateCustomer
from src.commands.validate_document import ValidateDocument
from src.commands.assign_salesperson_to_customer import AssignSalespersonToCustomer

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


@customers_bp.route('', methods=['POST'])
def create_customer():
    """
    Registra un nuevo cliente en el sistema.
    
    Body (JSON):
        document_type (str): Tipo de documento (NIT, CC, CE, RUT, DNI) - Requerido
        document_number (str): Número de documento - Requerido
        business_name (str): Razón social - Requerido
        customer_type (str): Tipo de cliente (hospital, clinica, farmacia, distribuidor, ips, eps) - Requerido
        trade_name (str, opcional): Nombre comercial
        contact_name (str, opcional): Nombre del contacto
        contact_email (str, opcional): Email del contacto
        contact_phone (str, opcional): Teléfono del contacto
        address (str, opcional): Dirección
        neighborhood (str, opcional): Barrio
        city (str, opcional): Ciudad
        department (str, opcional): Departamento
        country (str, opcional): País (por defecto: Colombia)
        latitude (float, opcional): Latitud GPS (debe estar entre -90.0 y 90.0)
        longitude (float, opcional): Longitud GPS (debe estar entre -180.0 y 180.0)
        credit_limit (float, opcional): Límite de crédito (por defecto: 0.0)
        credit_days (int, opcional): Días de crédito (por defecto: 0)
        salesperson_id (int, opcional): ID del vendedor asignado
        is_active (bool, opcional): Estado activo (por defecto: true)
    
    Retorna:
        201: Cliente creado exitosamente
        400: Error de validación
        500: Error interno del servidor
    
    Ejemplo:
        POST /customers
        {
            "document_type": "NIT",
            "document_number": "900123456-7",
            "business_name": "Hospital San Juan",
            "customer_type": "hospital",
            "contact_name": "María González",
            "contact_email": "contacto@hospitalsanjuan.com",
            "contact_phone": "+57 1 234 5678",
            "address": "Calle 45 # 12-34",
            "salesperson_id": 5
            "neighborhood": "Chapinero",
            "city": "Bogotá",
            "department": "Cundinamarca",
            "latitude": 4.60971,
            "longitude": -74.08175,
            "credit_limit": 50000000.00,
            "credit_days": 30
        }
    """
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({
                'error': 'JSON data is required'
            }), 400
        
        command = CreateCustomer(data)
        customer = command.execute()
        
        return jsonify({
            'message': 'Customer created successfully',
            'customer': customer
        }), 201
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 400


@customers_bp.route('', methods=['GET'])
def get_customers():
    """
    Obtiene la lista de clientes con filtrado opcional.
    
    Parámetros de Query:
        customer_type (str, opcional): Filtrar por tipo de cliente (hospital, clinica, farmacia, distribuidor)
        city (str, opcional): Filtrar por ciudad
        is_active (bool, opcional): Filtrar por estado activo
    
    Retorna:
        200: Lista de clientes
        500: Error interno del servidor
    
    Ejemplo:
        GET /customers?customer_type=hospital&city=Bogotá&is_active=true
    """
    customer_type = request.args.get('customer_type')
    city = request.args.get('city')
    is_active_str = request.args.get('is_active')
    
    is_active = None
    if is_active_str:
        is_active = is_active_str.lower() in ['true', '1', 'yes']
    
    command = GetCustomers(
        customer_type=customer_type,
        city=city,
        is_active=is_active
    )
    
    customers = command.execute()
    
    return jsonify({
        'customers': customers,
        'total': len(customers)
    }), 200


@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    """
    Obtiene un cliente por ID.
    
    Parámetros de Path:
        customer_id (int): ID del cliente
    
    Retorna:
        200: Detalles del cliente
        404: Cliente no encontrado
    
    Ejemplo:
        GET /customers/1
    """
    command = GetCustomerById(customer_id)
    customer = command.execute()
    
    return jsonify(customer), 200


@customers_bp.route('/validate-document', methods=['GET'])
def validate_document():
    """
    Valida si un número de documento (RUC/NIT) ya existe en el sistema.
    
    Parámetros de Query:
        document_number (str, requerido): Número de documento a validar
        document_type (str, opcional): Tipo de documento (por defecto: "NIT")
    
    Retorna:
        200: Resultado de la validación
        400: Parámetros faltantes o inválidos
        500: Error interno del servidor
    
    Respuesta:
        {
            "exists": boolean,        // true si ya existe, false si está disponible
            "customer_id": int,       // ID del cliente si existe (null si no existe)
            "message": string         // Mensaje descriptivo
        }
    
    Ejemplo de uso:
        GET /customers/validate-document?document_number=900123456-7&document_type=NIT
        
        Respuesta si existe:
        {
            "exists": true,
            "customer_id": 1,
            "message": "Document NIT 900123456-7 is already registered to customer: Hospital San Juan"
        }
        
        Respuesta si NO existe:
        {
            "exists": false,
            "customer_id": null,
            "message": "Document NIT 900123456-7 is available for registration"
        }
    """
    try:
        document_number = request.args.get('document_number')
        document_type = request.args.get('document_type', 'NIT')
        
        if not document_number:
            return jsonify({
                'error': 'document_number parameter is required'
            }), 400
        
        command = ValidateDocument(document_number, document_type)
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValueError as e:
        return jsonify({
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500


@customers_bp.route('/<int:customer_id>/assign-salesperson', methods=['PUT'])
def assign_salesperson(customer_id):
    """
    Asignar o actualizar el vendedor asignado a un cliente.
    
    Args:
        customer_id (int): ID del cliente
    
    Body (JSON):
        salesperson_id (int or null): ID del vendedor a asignar (null para desasignar)
    
    Retorna:
        200: Vendedor asignado exitosamente
        400: Error de validación
        404: Cliente o vendedor no encontrado
        500: Error interno del servidor
    
    Ejemplo:
        PUT /customers/1/assign-salesperson
        {
            "salesperson_id": 5
        }
        
        # Para desasignar:
        {
            "salesperson_id": null
        }
    """
    try:
        data = request.get_json()
        
        if 'salesperson_id' not in data:
            return jsonify({
                'error': 'salesperson_id is required in request body'
            }), 400
        
        salesperson_id = data['salesperson_id']
        
        # Execute command
        command = AssignSalespersonToCustomer(customer_id, salesperson_id)
        result = command.execute()
        
        action = 'assigned' if salesperson_id else 'unassigned'
        
        return jsonify({
            'message': f'Salesperson {action} successfully',
            'customer': result
        }), 200
        
    except Exception as e:
        from src.errors.errors import ValidationError, NotFoundError
        
        if isinstance(e, NotFoundError):
            return jsonify({'error': str(e)}), 404
        elif isinstance(e, ValidationError):
            return jsonify({'error': str(e)}), 400
        else:
            return jsonify({
                'error': f'An error occurred: {str(e)}'
            }), 500


@customers_bp.route('/by-salesperson/<int:salesperson_id>', methods=['GET'])
def get_customers_by_salesperson(salesperson_id):
    """
    Obtener todos los clientes asignados a un vendedor específico.
    
    Args:
        salesperson_id (int): ID del vendedor
    
    Query Parameters:
        is_active (bool, opcional): Filtrar por estado activo/inactivo
        page (int, opcional): Número de página (por defecto: 1)
        per_page (int, opcional): Resultados por página (por defecto: 50)
    
    Retorna:
        200: Lista de clientes
        500: Error interno del servidor
    
    Ejemplo:
        GET /customers/by-salesperson/5?is_active=true&page=1&per_page=20
    """
    try:
        from src.models.customer import Customer
        
        # Get query parameters
        is_active = request.args.get('is_active')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Build query
        query = Customer.query.filter_by(salesperson_id=salesperson_id)
        
        # Apply filters
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            query = query.filter_by(is_active=is_active_bool)
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'customers': [customer.to_dict() for customer in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'total_pages': pagination.pages
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@customers_bp.route('/batch', methods=['POST'])
def get_customers_batch():
    """
    Obtiene múltiples clientes por sus IDs (batch request).
    
    Útil para logistics-service al generar rutas de visitas.
    
    Body (JSON):
        customer_ids (List[int]): Lista de IDs de clientes a obtener - Requerido
    
    Retorna:
        200: Clientes encontrados
        {
            "customers": [
                {
                    "id": 1,
                    "business_name": "Farmacia San Rafael",
                    "document_type": "NIT",
                    "document_number": "900123456-1",
                    "customer_type": "farmacia",
                    "address": "Calle 50 #20-30",
                    "latitude": 4.6486259,
                    "longitude": -74.0628451,
                    ...
                }
            ],
            "total": 1,
            "not_found": [],
            "requested": 1
        }
        400: Error de validación
        500: Error interno del servidor
    
    Ejemplo:
        POST /customers/batch
        {
            "customer_ids": [1, 5, 12, 45]
        }
    """
    try:
        from src.models.customer import Customer
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        customer_ids = data.get('customer_ids')
        
        if not customer_ids:
            return jsonify({'error': 'customer_ids is required'}), 400
        
        if not isinstance(customer_ids, list):
            return jsonify({'error': 'customer_ids must be an array'}), 400
        
        if not customer_ids:
            return jsonify({
                'customers': [],
                'total': 0,
                'not_found': [],
                'requested': 0
            }), 200
        
        # Validar que todos sean enteros
        try:
            customer_ids = [int(cid) for cid in customer_ids]
        except (ValueError, TypeError):
            return jsonify({'error': 'All customer_ids must be integers'}), 400
        
        # Obtener clientes
        customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
        
        # Identificar cuáles no se encontraron
        found_ids = {customer.id for customer in customers}
        not_found = [cid for cid in customer_ids if cid not in found_ids]
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers],
            'total': len(customers),
            'not_found': not_found,
            'requested': len(customer_ids)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500


@customers_bp.route('/health', methods=['GET'])
def health_check():
    """
    Endpoint de health check para el servicio de clientes.
    
    Retorna:
        200: El servicio está saludable
    """
    return jsonify({
        'service': 'sales-service',
        'module': 'customers',
        'status': 'healthy',
        'version': '1.0.0'
    }), 200
