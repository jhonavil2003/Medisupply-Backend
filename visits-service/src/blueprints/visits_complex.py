from flask import Blueprint, request, jsonify
from src.commands.create_visit import CreateVisit
from src.commands.get_visits import GetVisits
from src.commands.get_visit_by_id import GetVisitById
from src.commands.update_visit import UpdateVisit
from src.commands.delete_visit import DeleteVisit
from src.commands.get_visit_stats import GetVisitStats
from src.dtos.create_visit_request import CreateVisitRequest
from src.dtos.update_visit_request import UpdateVisitRequest
from src.dtos.visit_filters_and_utils import VisitFilterRequest
from src.errors.errors import ValidationError, NotFoundError
from pydantic import ValidationError as PydanticValidationError

visits_bp = Blueprint('visits', __name__, url_prefix='/api/visits')


@visits_bp.route('', methods=['POST'])
def create_visit():
    """Crear una nueva visita"""
    try:
        # Validar datos de entrada
        visit_data = CreateVisitRequest(**request.get_json())
        
        # Ejecutar comando
        command = CreateVisit()
        result = command.execute(visit_data)
        
        return jsonify({
            'message': 'Visita creada exitosamente',
            'visit': result.to_dict()
        }), 201
        
    except PydanticValidationError as e:
        raise ValidationError(f"Error de validación: {str(e)}")
    except Exception as e:
        raise ValidationError(f"Error al crear visita: {str(e)}")


@visits_bp.route('', methods=['GET'])
def get_visits():
    """Obtener lista de visitas con filtros opcionales"""
    try:
        # Obtener parámetros de query
        query_params = request.args.to_dict()
        
        # Crear filtro con valores por defecto
        filter_request = VisitFilterRequest(
            customer_id=query_params.get('customer_id'),
            salesperson_id=query_params.get('salesperson_id'),
            status=query_params.get('status'),
            start_date=query_params.get('start_date'),
            end_date=query_params.get('end_date'),
            page=int(query_params.get('page', 1)),
            per_page=int(query_params.get('per_page', 10)),
            sort_by=query_params.get('sort_by', 'visit_date'),
            sort_order=query_params.get('sort_order', 'desc')
        )
        
        # Ejecutar comando
        command = GetVisits()
        result = command.execute(filter_request)
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        raise ValidationError(f"Error al obtener visitas: {str(e)}")


@visits_bp.route('/<int:visit_id>', methods=['GET'])
def get_visit_by_id(visit_id):
    """Obtener una visita por ID"""
    try:
        command = GetVisitById()
        result = command.execute(visit_id)
        
        if not result:
            raise NotFoundError(f"Visita con ID {visit_id} no encontrada")
            
        return jsonify({
            'visit': result.to_dict(include_files=True, include_salesperson=True)
        }), 200
        
    except NotFoundError:
        raise
    except Exception as e:
        raise ValidationError(f"Error al obtener visita: {str(e)}")


@visits_bp.route('/<int:visit_id>', methods=['PUT'])
def update_visit(visit_id):
    """Actualizar una visita"""
    try:
        # Validar datos de entrada
        update_data = UpdateVisitRequest(**request.get_json())
        
        # Ejecutar comando
        command = UpdateVisit()
        result = command.execute(visit_id, update_data)
        
        if not result:
            raise NotFoundError(f"Visita con ID {visit_id} no encontrada")
            
        return jsonify({
            'message': 'Visita actualizada exitosamente',
            'visit': result.to_dict()
        }), 200
        
    except PydanticValidationError as e:
        raise ValidationError(f"Error de validación: {str(e)}")
    except NotFoundError:
        raise
    except Exception as e:
        raise ValidationError(f"Error al actualizar visita: {str(e)}")


@visits_bp.route('/<int:visit_id>', methods=['DELETE'])
def delete_visit(visit_id):
    """Eliminar una visita (soft delete)"""
    try:
        command = DeleteVisit()
        success = command.execute(visit_id)
        
        if not success:
            raise NotFoundError(f"Visita con ID {visit_id} no encontrada")
            
        return jsonify({
            'message': f'Visita {visit_id} eliminada exitosamente'
        }), 200
        
    except NotFoundError:
        raise
    except Exception as e:
        raise ValidationError(f"Error al eliminar visita: {str(e)}")


@visits_bp.route('/stats', methods=['GET'])
def get_visit_stats():
    """Obtener estadísticas de visitas"""
    try:
        # Obtener parámetros opcionales
        salesperson_id = request.args.get('salesperson_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        command = GetVisitStats()
        result = command.execute(salesperson_id, start_date, end_date)
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        raise ValidationError(f"Error al obtener estadísticas: {str(e)}")


@visits_bp.route('/salesperson/<int:salesperson_id>', methods=['GET'])
def get_visits_by_salesperson(salesperson_id):
    """Obtener visitas de un vendedor específico"""
    try:
        # Crear filtro específico para vendedor
        filter_request = VisitFilterRequest(
            salesperson_id=salesperson_id,
            page=int(request.args.get('page', 1)),
            per_page=int(request.args.get('per_page', 10)),
            sort_by=request.args.get('sort_by', 'visit_date'),
            sort_order=request.args.get('sort_order', 'desc')
        )
        
        command = GetVisits()
        result = command.execute(filter_request)
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        raise ValidationError(f"Error al obtener visitas del vendedor: {str(e)}")


@visits_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_visits_by_customer(customer_id):
    """Obtener visitas de un cliente específico"""
    try:
        # Crear filtro específico para cliente
        filter_request = VisitFilterRequest(
            customer_id=customer_id,
            page=int(request.args.get('page', 1)),
            per_page=int(request.args.get('per_page', 10)),
            sort_by=request.args.get('sort_by', 'visit_date'),
            sort_order=request.args.get('sort_order', 'desc')
        )
        
        command = GetVisits()
        result = command.execute(filter_request)
        
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        raise ValidationError(f"Error al obtener visitas del cliente: {str(e)}")