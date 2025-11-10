"""
Blueprint para gestión de objetivos de vendedores (Salesperson Goals)
Endpoints CRUD para objetivos de ventas
"""

from flask import Blueprint, request, jsonify
from src.commands.create_salesperson_goal import CreateSalespersonGoal
from src.commands.get_salesperson_goals import GetSalespersonGoals
from src.commands.get_salesperson_goal_by_id import GetSalespersonGoalById
from src.commands.update_salesperson_goal import UpdateSalespersonGoal
from src.commands.delete_salesperson_goal import DeleteSalespersonGoal
from src.errors.errors import ValidationError, ApiError
from src.session import db

salesperson_goals_bp = Blueprint('salesperson_goals', __name__, url_prefix='/salesperson-goals')


@salesperson_goals_bp.route('/', methods=['POST'])
def create_goal():
    """
    POST /salesperson-goals/
    
    Crear un nuevo objetivo de venta para un vendedor
    
    Request Body:
    {
        "id_vendedor": "EMP001",
        "id_producto": "MED-001-2024",
        "region": "Norte",
        "trimestre": "Q1",
        "valor_objetivo": 50000.00,
        "tipo": "monetario"
    }
    
    Returns:
    - 201: Objetivo creado exitosamente
    - 400: Validación fallida
    - 500: Error del servidor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionó ningún dato'}), 400
        
        command = CreateSalespersonGoal(data)
        result = command.execute()
        
        return jsonify({
            'message': 'Objetivo creado exitosamente',
            'goal': result
        }), 201
        
    except ValidationError as e:
        raise e
    except ApiError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise ApiError(f'Error al crear objetivo: {str(e)}', status_code=500)


@salesperson_goals_bp.route('/', methods=['GET'])
def get_goals():
    """
    GET /salesperson-goals/
    
    Obtener lista de objetivos con filtros opcionales
    
    Query Parameters:
    - id_vendedor: Filtrar por ID de vendedor
    - id_producto: Filtrar por SKU de producto
    - region: Filtrar por región (Norte/Sur/Oeste/Este)
    - trimestre: Filtrar por trimestre (Q1/Q2/Q3/Q4)
    - tipo: Filtrar por tipo (unidades/monetario)
    
    Returns:
    - 200: Lista de objetivos
    - 500: Error del servidor
    
    Example:
    GET /salesperson-goals/?id_vendedor=EMP001&trimestre=Q1
    """
    try:
        filters = {
            'id_vendedor': request.args.get('id_vendedor'),
            'id_producto': request.args.get('id_producto'),
            'region': request.args.get('region'),
            'trimestre': request.args.get('trimestre'),
            'tipo': request.args.get('tipo')
        }
        
        command = GetSalespersonGoals(filters)
        result = command.execute()
        
        return jsonify({
            'goals': result,
            'total': len(result)
        }), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f'Error al obtener objetivos: {str(e)}', status_code=500)


@salesperson_goals_bp.route('/<int:goal_id>', methods=['GET'])
def get_goal_by_id(goal_id):
    """
    GET /salesperson-goals/{goal_id}
    
    Obtener un objetivo específico por ID
    
    Path Parameters:
    - goal_id: ID del objetivo (requerido)
    
    Returns:
    - 200: Objetivo encontrado
    - 404: Objetivo no encontrado
    - 500: Error del servidor
    
    Example:
    GET /salesperson-goals/1
    """
    try:
        command = GetSalespersonGoalById(goal_id)
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        raise e
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f'Error al obtener objetivo: {str(e)}', status_code=500)


@salesperson_goals_bp.route('/<int:goal_id>', methods=['PUT'])
def update_goal(goal_id):
    """
    PUT /salesperson-goals/{goal_id}
    
    Actualizar un objetivo existente
    
    Path Parameters:
    - goal_id: ID del objetivo (requerido)
    
    Request Body (todos los campos son opcionales):
    {
        "id_vendedor": "EMP002",
        "id_producto": "MED-002-2024",
        "region": "Sur",
        "trimestre": "Q2",
        "valor_objetivo": 75000.00,
        "tipo": "unidades"
    }
    
    Returns:
    - 200: Objetivo actualizado exitosamente
    - 400: Validación fallida
    - 404: Objetivo no encontrado
    - 500: Error del servidor
    
    Example:
    PUT /salesperson-goals/1
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se proporcionó ningún dato'}), 400
        
        command = UpdateSalespersonGoal(goal_id, data)
        result = command.execute()
        
        return jsonify({
            'message': 'Objetivo actualizado exitosamente',
            'goal': result
        }), 200
        
    except ValidationError as e:
        raise e
    except ApiError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise ApiError(f'Error al actualizar objetivo: {str(e)}', status_code=500)


@salesperson_goals_bp.route('/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    """
    DELETE /salesperson-goals/{goal_id}
    
    Eliminar un objetivo
    
    Path Parameters:
    - goal_id: ID del objetivo (requerido)
    
    Returns:
    - 200: Objetivo eliminado exitosamente
    - 404: Objetivo no encontrado
    - 500: Error del servidor
    
    Example:
    DELETE /salesperson-goals/1
    """
    try:
        command = DeleteSalespersonGoal(goal_id)
        result = command.execute()
        
        return jsonify(result), 200
        
    except ValidationError as e:
        raise e
    except ApiError as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise ApiError(f'Error al eliminar objetivo: {str(e)}', status_code=500)


# Endpoint adicional: Obtener objetivos por vendedor
@salesperson_goals_bp.route('/vendedor/<string:employee_id>', methods=['GET'])
def get_goals_by_salesperson(employee_id):
    """
    GET /salesperson-goals/vendedor/{employee_id}
    
    Obtener todos los objetivos de un vendedor específico
    
    Path Parameters:
    - employee_id: ID del vendedor
    
    Query Parameters (opcionales):
    - trimestre: Filtrar por trimestre
    - region: Filtrar por región
    
    Returns:
    - 200: Lista de objetivos del vendedor
    - 500: Error del servidor
    
    Example:
    GET /salesperson-goals/vendedor/EMP001?trimestre=Q1
    """
    try:
        filters = {
            'id_vendedor': employee_id,
            'trimestre': request.args.get('trimestre'),
            'region': request.args.get('region')
        }
        
        command = GetSalespersonGoals(filters)
        result = command.execute()
        
        return jsonify({
            'employee_id': employee_id,
            'goals': result,
            'total': len(result)
        }), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f'Error al obtener objetivos del vendedor: {str(e)}', status_code=500)


# Endpoint adicional: Obtener objetivos por producto
@salesperson_goals_bp.route('/producto/<string:product_sku>', methods=['GET'])
def get_goals_by_product(product_sku):
    """
    GET /salesperson-goals/producto/{product_sku}
    
    Obtener todos los objetivos asociados a un producto específico
    
    Path Parameters:
    - product_sku: SKU del producto
    
    Query Parameters (opcionales):
    - trimestre: Filtrar por trimestre
    - region: Filtrar por región
    
    Returns:
    - 200: Lista de objetivos del producto
    - 500: Error del servidor
    
    Example:
    GET /salesperson-goals/producto/MED-001-2024?trimestre=Q1
    """
    try:
        filters = {
            'id_producto': product_sku,
            'trimestre': request.args.get('trimestre'),
            'region': request.args.get('region')
        }
        
        command = GetSalespersonGoals(filters)
        result = command.execute()
        
        return jsonify({
            'product_sku': product_sku,
            'goals': result,
            'total': len(result)
        }), 200
        
    except ApiError as e:
        raise e
    except Exception as e:
        raise ApiError(f'Error al obtener objetivos del producto: {str(e)}', status_code=500)
