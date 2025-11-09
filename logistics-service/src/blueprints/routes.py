"""
Blueprint para gestión de rutas de entrega optimizadas.

Endpoints:
- POST /routes/generate - Generar rutas optimizadas
- GET /routes - Listar rutas con filtros
- GET /routes/<id> - Detalle de ruta
- GET /routes/date/<date> - Rutas por fecha
- PUT /routes/<id>/status - Actualizar estado
- DELETE /routes/<id> - Cancelar ruta
- POST /routes/<id>/reassign - Reasignar pedido
- GET /vehicles - Listar vehículos
- GET /vehicles/available - Vehículos disponibles
- GET /vehicles/<id> - Detalle de vehículo
- PUT /vehicles/<id>/availability - Actualizar disponibilidad
"""

from flask import Blueprint, request, jsonify, make_response
from datetime import datetime
import logging

from src.commands.generate_routes import GenerateRoutesCommand, CancelRoute, UpdateRouteStatus
from src.commands.get_routes import GetRoutes, GetRouteById, GetRoutesByDate
from src.commands.get_vehicles import (
    GetVehicles,
    GetVehicleById,
    UpdateVehicleAvailability,
    GetAvailableVehicles
)
from src.commands.reassign_order import ReassignOrder
from src.services.export_service import get_export_service

logger = logging.getLogger(__name__)

routes_bp = Blueprint('routes', __name__, url_prefix='/routes')
vehicles_bp = Blueprint('vehicles', __name__, url_prefix='/vehicles')


# ===========================
# RUTAS - ENDPOINTS
# ===========================

@routes_bp.route('/generate', methods=['POST'])
def generate_routes():
    """
    POST /routes/generate
    
    Genera rutas optimizadas a partir de IDs de órdenes.
    
    **NUEVO**: Versión simplificada que recibe solo IDs de órdenes y obtiene
    los detalles automáticamente desde sales-service.
    
    Request Body:
    {
        "distribution_center_id": 1,
        "planned_date": "2025-11-10",
        "order_ids": [101, 102, 103, 104, 105],
        "optimization_strategy": "balanced",  // opcional (DEFAULT - RECOMENDADO)
        "force_regenerate": false             // opcional
    }
    
    Estrategias de optimización disponibles:
    - 'balanced': Balance entre distancia, tiempo, capacidad y equidad (DEFAULT - RECOMENDADO)
    - 'minimize_distance': Minimiza distancia y consumo de gasolina
    - 'minimize_time': Prioriza minimizar tiempo de entrega
    - 'minimize_cost': Minimiza costo operativo total
    - 'priority_first': Entrega primero a clientes críticos
    
    Response Body (RESUMIDO):
    {
        "status": "success",
        "summary": {
            "routes_generated": 2,
            "orders_assigned": 5,
            "orders_unassigned": 0,
            "total_distance_km": 45.3,
            "estimated_duration_hours": 2.5,
            "optimization_score": 87.5
        },
        "routes": [
            {
                "id": 123,
                "route_code": "ROUTE-20251110-DC1-001",
                "vehicle": {
                    "id": 10,
                    "plate": "ABC-123",
                    "type": "refrigerated_truck"
                },
                "stops_count": 3,
                "orders_count": 3,
                "distance_km": 22.5,
                "duration_minutes": 75,
                "status": "draft"
            }
        ],
        "warnings": [],
        "errors": [],
        "computation_time_seconds": 12.3
    }
    
    Posibles status:
    - 'success': Todas las órdenes fueron asignadas
    - 'partial': Algunas órdenes no pudieron ser asignadas
    - 'failed': Error en el proceso
    - 'no_orders': No se proporcionaron IDs de órdenes
    - 'no_orders_found': Ninguna orden encontrada en sales-service
    - 'no_valid_orders': Ninguna orden cumple requisitos
    - 'no_vehicles': No hay vehículos disponibles
    - 'existing_routes': Ya existen rutas para la fecha (use force_regenerate)
    - 'sales_service_unavailable': Sales-service no responde
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        if not data:
            return jsonify({
                'error': 'Request body is required',
                'status_code': 400
            }), 400
        
        if not data.get('distribution_center_id'):
            return jsonify({
                'error': 'distribution_center_id es requerido',
                'status_code': 400
            }), 400
        
        if not data.get('planned_date'):
            return jsonify({
                'error': 'planned_date es requerido',
                'status_code': 400
            }), 400
        
        if 'order_ids' not in data:
            return jsonify({
                'error': 'order_ids es requerido',
                'status_code': 400
            }), 400
        
        if not isinstance(data['order_ids'], list):
            return jsonify({
                'error': 'order_ids debe ser un array de enteros',
                'status_code': 400
            }), 400
        
        # Parsear fecha
        try:
            planned_date = datetime.strptime(data['planned_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'planned_date debe estar en formato YYYY-MM-DD',
                'status_code': 400
            }), 400
        
        # Validar estrategia de optimización
        valid_strategies = ['balanced', 'minimize_time', 'minimize_distance', 'minimize_cost', 'priority_first']
        optimization_strategy = data.get('optimization_strategy', 'balanced')
        
        if optimization_strategy not in valid_strategies:
            return jsonify({
                'error': f'optimization_strategy debe ser uno de: {", ".join(valid_strategies)}',
                'status_code': 400
            }), 400
        
        # Crear comando
        command = GenerateRoutesCommand(
            distribution_center_id=data['distribution_center_id'],
            order_ids=data['order_ids'],
            planned_date=planned_date,
            optimization_strategy=optimization_strategy,
            force_regenerate=data.get('force_regenerate', False),
            created_by=data.get('created_by', 'api_user')
        )
        
        # Ejecutar
        result = command.execute()
        
        # Determinar código de respuesta HTTP
        status_code_map = {
            'success': 200,
            'partial': 200,
            'no_orders': 400,
            'no_orders_found': 404,
            'no_valid_orders': 400,
            'no_vehicles': 409,
            'existing_routes': 409,
            'sales_service_unavailable': 503,
            'optimization_failed': 500,
            'failed': 500
        }
        
        status_code = status_code_map.get(result['status'], 200)
        
        return jsonify(result), status_code
    
    except Exception as e:
        logger.exception(f"Error en endpoint /routes/generate: {e}")
        return jsonify({
            'status': 'failed',
            'error': 'Error interno del servidor',
            'message': str(e),
            'status_code': 500
        }), 500


@routes_bp.route('', methods=['GET'])
def get_routes():
    """
    GET /routes?distribution_center_id=1&planned_date=2025-11-05&status=active&limit=50&offset=0
    
    Lista rutas con filtros y paginación.
    """
    try:
        # Obtener parámetros de query
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        planned_date_str = request.args.get('planned_date')
        status = request.args.get('status')
        vehicle_id = request.args.get('vehicle_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Parsear fecha si existe
        planned_date = None
        if planned_date_str:
            try:
                planned_date = datetime.strptime(planned_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': 'planned_date debe estar en formato YYYY-MM-DD'
                }), 400
        
        # Crear comando
        command = GetRoutes(
            distribution_center_id=distribution_center_id,
            planned_date=planned_date,
            status=status,
            vehicle_id=vehicle_id,
            limit=limit,
            offset=offset
        )
        
        # Ejecutar
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint /routes: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@routes_bp.route('/<int:route_id>', methods=['GET'])
def get_route_detail(route_id):
    """
    GET /routes/<id>?summary=true&include_stops=true&include_assignments=true
    
    Obtiene detalle de una ruta.
    
    Query params:
    - summary: true (default) = respuesta resumida y compacta
               false = respuesta completa con todos los detalles
    - include_stops: true/false (solo aplica cuando summary=false)
    - include_assignments: true/false (solo aplica cuando summary=false)
    
    Ejemplo resumido (summary=true - DEFAULT):
    {
        "status": "success",
        "route": {
            "id": 3,
            "route_code": "ROUTE-20251109-DC1-003",
            "status": "draft",
            "vehicle": {"plate": "ABC-123", "type": "refrigerated_truck"},
            "metrics": {
                "total_stops": 9,
                "total_orders": 9,
                "total_distance_km": 51.34,
                "estimated_duration_minutes": 1097
            },
            "stops": [
                {
                    "sequence": 1,
                    "address": "Carrera 22 #39-80",
                    "city": "Bogotá",
                    "orders": [{"order_number": "ORD-001", "customer_name": "Cliente X"}]
                }
            ]
        }
    }
    """
    try:
        # Por defecto, usar modo resumido
        summary_mode = request.args.get('summary', 'true').lower() == 'true'
        include_stops = request.args.get('include_stops', 'true').lower() == 'true'
        include_assignments = request.args.get('include_assignments', 'true').lower() == 'true'
        
        command = GetRouteById(
            route_id=route_id,
            include_stops=include_stops,
            include_assignments=include_assignments,
            summary_mode=summary_mode
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] == 'not_found':
            return jsonify(result), 404
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint /routes/{route_id}: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@routes_bp.route('/date/<date_str>', methods=['GET'])
def get_routes_by_date(date_str):
    """
    GET /routes/date/<YYYY-MM-DD>?distribution_center_id=1
    
    Obtiene todas las rutas de una fecha específica con métricas.
    """
    try:
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        
        if not distribution_center_id:
            return jsonify({
                'error': 'distribution_center_id es requerido'
            }), 400
        
        # Parsear fecha
        try:
            planned_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'Fecha debe estar en formato YYYY-MM-DD'
            }), 400
        
        command = GetRoutesByDate(
            distribution_center_id=distribution_center_id,
            planned_date=planned_date
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint /routes/date/{date_str}: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@routes_bp.route('/<int:route_id>/status', methods=['PUT'])
def update_route_status(route_id):
    """
    PUT /routes/<id>/status
    
    Actualiza el estado de una ruta.
    
    Body:
    {
        "status": "active",
        "updated_by": "usuario@example.com"
    }
    """
    try:
        data = request.get_json()
        
        if not data.get('status'):
            return jsonify({
                'error': 'status es requerido'
            }), 400
        
        valid_statuses = ['draft', 'active', 'in_progress', 'completed', 'cancelled']
        if data['status'] not in valid_statuses:
            return jsonify({
                'error': f'status debe ser uno de: {", ".join(valid_statuses)}'
            }), 400
        
        command = UpdateRouteStatus(
            route_id=route_id,
            new_status=data['status'],
            updated_by=data.get('updated_by', 'api')
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] == 'error':
            return jsonify(result), 400
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint PUT /routes/{route_id}/status: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@routes_bp.route('/<int:route_id>', methods=['DELETE'])
def cancel_route(route_id):
    """
    DELETE /routes/<id>
    
    Cancela una ruta.
    
    Body:
    {
        "reason": "Vehículo averiado",
        "cancelled_by": "usuario@example.com"
    }
    """
    try:
        data = request.get_json() or {}
        
        if not data.get('reason'):
            return jsonify({
                'error': 'reason es requerido'
            }), 400
        
        command = CancelRoute(
            route_id=route_id,
            reason=data['reason'],
            cancelled_by=data.get('cancelled_by', 'api')
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] in ['error', 'warning']:
            return jsonify(result), 400
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint DELETE /routes/{route_id}: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@routes_bp.route('/<int:route_id>/reassign', methods=['POST'])
def reassign_order(route_id):
    """
    POST /routes/<id>/reassign
    
    Reasigna un pedido a otro vehículo.
    
    Body:
    {
        "order_id": 123,
        "new_vehicle_id": 2,
        "reason": "Vehículo con capacidad insuficiente",
        "reassigned_by": "usuario@example.com"
    }
    """
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['order_id', 'new_vehicle_id', 'reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'error': f'{field} es requerido'
                }), 400
        
        command = ReassignOrder(
            order_id=data['order_id'],
            current_route_id=route_id,
            new_vehicle_id=data['new_vehicle_id'],
            reason=data['reason'],
            reassigned_by=data.get('reassigned_by', 'api')
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] in ['not_found', 'validation_error']:
            return jsonify(result), 400
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint POST /routes/{route_id}/reassign: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


# ===========================
# VEHÍCULOS - ENDPOINTS
# ===========================

@vehicles_bp.route('', methods=['GET'])
def get_vehicles():
    """
    GET /vehicles?distribution_center_id=1&is_available=true&has_refrigeration=true
    
    Lista vehículos con filtros.
    """
    try:
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        is_available = request.args.get('is_available')
        has_refrigeration = request.args.get('has_refrigeration')
        vehicle_type = request.args.get('vehicle_type')
        
        # Convertir strings a boolean
        if is_available is not None:
            is_available = is_available.lower() == 'true'
        
        if has_refrigeration is not None:
            has_refrigeration = has_refrigeration.lower() == 'true'
        
        command = GetVehicles(
            distribution_center_id=distribution_center_id,
            is_available=is_available,
            has_refrigeration=has_refrigeration,
            vehicle_type=vehicle_type
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint /vehicles: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@vehicles_bp.route('/available', methods=['GET'])
def get_available_vehicles():
    """
    GET /vehicles/available?distribution_center_id=1&planned_date=2025-11-05
    
    Obtiene vehículos disponibles para una fecha específica.
    """
    try:
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        planned_date_str = request.args.get('planned_date')
        
        if not distribution_center_id:
            return jsonify({
                'error': 'distribution_center_id es requerido'
            }), 400
        
        # Parsear fecha si existe
        planned_date = None
        if planned_date_str:
            try:
                planned_date = datetime.strptime(planned_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'error': 'planned_date debe estar en formato YYYY-MM-DD'
                }), 400
        
        command = GetAvailableVehicles(
            distribution_center_id=distribution_center_id,
            planned_date=planned_date
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint /vehicles/available: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@vehicles_bp.route('/<int:vehicle_id>', methods=['GET'])
def get_vehicle_detail(vehicle_id):
    """
    GET /vehicles/<id>
    
    Obtiene detalle de un vehículo.
    """
    try:
        command = GetVehicleById(vehicle_id=vehicle_id)
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] == 'not_found':
            return jsonify(result), 404
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint /vehicles/{vehicle_id}: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@vehicles_bp.route('/<int:vehicle_id>/availability', methods=['PUT'])
def update_vehicle_availability(vehicle_id):
    """
    PUT /vehicles/<id>/availability
    
    Actualiza la disponibilidad de un vehículo.
    
    Body:
    {
        "is_available": false,
        "reason": "Mantenimiento programado"
    }
    """
    try:
        data = request.get_json()
        
        if 'is_available' not in data:
            return jsonify({
                'error': 'is_available es requerido'
            }), 400
        
        command = UpdateVehicleAvailability(
            vehicle_id=vehicle_id,
            is_available=data['is_available'],
            reason=data.get('reason')
        )
        
        result = command.execute()
        
        if result['status'] == 'success':
            return jsonify(result), 200
        elif result['status'] == 'not_found':
            return jsonify(result), 404
        else:
            return jsonify(result), 500
    
    except Exception as e:
        logger.exception(f"Error en endpoint PUT /vehicles/{vehicle_id}/availability: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


# ===========================
# EXPORTACIÓN - ENDPOINTS
# ===========================

@routes_bp.route('/<int:route_id>/export', methods=['GET'])
def export_route(route_id):
    """
    GET /routes/<id>/export?format=pdf|csv
    
    Exporta una ruta en el formato especificado.
    
    Formatos soportados:
    - pdf: Hoja de ruta detallada para conductores
    - csv: Datos tabulares para análisis
    
    Query Parameters:
    - format: pdf o csv (requerido)
    
    Response:
    - Content-Type: application/pdf o text/csv
    - Content-Disposition: attachment con nombre de archivo
    """
    try:
        # Obtener formato
        export_format = request.args.get('format', '').lower()
        
        if not export_format:
            return jsonify({
                'error': 'Parámetro format es requerido (pdf o csv)'
            }), 400
        
        if export_format not in ['pdf', 'csv']:
            return jsonify({
                'error': 'Formato no soportado. Use pdf o csv'
            }), 400
        
        export_service = get_export_service()
        
        if export_format == 'pdf':
            # Exportar a PDF
            try:
                pdf_content = export_service.export_route_to_pdf(route_id)
                
                # Crear respuesta con PDF
                response = make_response(pdf_content)
                response.headers['Content-Type'] = 'application/pdf'
                response.headers['Content-Disposition'] = f'attachment; filename=ruta_{route_id}.pdf'
                
                logger.info(f"PDF exportado para ruta {route_id}")
                return response
            
            except ValueError as e:
                return jsonify({
                    'error': str(e)
                }), 404
        
        elif export_format == 'csv':
            # Exportar a CSV
            try:
                csv_content = export_service.export_route_to_csv(route_id)
                
                # Crear respuesta con CSV
                response = make_response(csv_content)
                response.headers['Content-Type'] = 'text/csv; charset=utf-8'
                response.headers['Content-Disposition'] = f'attachment; filename=ruta_{route_id}.csv'
                
                logger.info(f"CSV exportado para ruta {route_id}")
                return response
            
            except ValueError as e:
                return jsonify({
                    'error': str(e)
                }), 404
    
    except Exception as e:
        logger.exception(f"Error exportando ruta {route_id}: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500


@routes_bp.route('/export/daily-summary', methods=['GET'])
def export_daily_summary():
    """
    GET /routes/export/daily-summary?distribution_center_id=1&date=2025-11-05
    
    Genera un resumen ejecutivo en PDF de todas las rutas del día.
    
    Query Parameters:
    - distribution_center_id: ID del centro de distribución (requerido)
    - date: Fecha en formato YYYY-MM-DD (requerido)
    
    Response:
    - Content-Type: application/pdf
    - Content-Disposition: attachment con nombre de archivo
    """
    try:
        # Obtener parámetros
        distribution_center_id = request.args.get('distribution_center_id', type=int)
        date_str = request.args.get('date')
        
        if not distribution_center_id:
            return jsonify({
                'error': 'distribution_center_id es requerido'
            }), 400
        
        if not date_str:
            return jsonify({
                'error': 'date es requerido'
            }), 400
        
        # Parsear fecha
        try:
            planned_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'error': 'date debe estar en formato YYYY-MM-DD'
            }), 400
        
        # Generar resumen
        export_service = get_export_service()
        
        try:
            pdf_content = export_service.export_daily_routes_summary(
                distribution_center_id=distribution_center_id,
                planned_date=planned_date
            )
            
            # Crear respuesta con PDF
            response = make_response(pdf_content)
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = (
                f'attachment; filename=resumen_rutas_{date_str}.pdf'
            )
            
            logger.info(
                f"Resumen diario exportado para DC {distribution_center_id} "
                f"fecha {date_str}"
            )
            return response
        
        except ValueError as e:
            return jsonify({
                'error': str(e)
            }), 404
    
    except Exception as e:
        logger.exception(f"Error exportando resumen diario: {e}")
        return jsonify({
            'error': 'Error interno del servidor',
            'message': str(e)
        }), 500
