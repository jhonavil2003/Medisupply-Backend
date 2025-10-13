from flask import Blueprint, request, jsonify
from src.commands.get_customers import GetCustomers
from src.commands.get_customer_by_id import GetCustomerById

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')


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
