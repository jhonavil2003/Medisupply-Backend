from flask import Blueprint, request, jsonify
from src.commands.get_customers import GetCustomers
from src.commands.get_customer_by_id import GetCustomerById
from src.commands.create_customer import CreateCustomer

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
        city (str, opcional): Ciudad
        department (str, opcional): Departamento
        country (str, opcional): País (por defecto: Colombia)
        credit_limit (float, opcional): Límite de crédito (por defecto: 0.0)
        credit_days (int, opcional): Días de crédito (por defecto: 0)
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
            "city": "Bogotá",
            "department": "Cundinamarca",
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
