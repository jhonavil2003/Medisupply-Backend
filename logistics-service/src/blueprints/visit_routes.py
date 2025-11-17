"""
Blueprint para gestión de rutas de visitas a clientes.

Endpoints para que vendedores generen y gestionen rutas optimizadas
para visitar múltiples clientes en una jornada.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date, time
import logging

from src.commands.generate_visit_routes import GenerateVisitRoutesCommand
from src.models.visit_route import VisitRoute, VisitRouteStatus
from src.models.visit_route_stop import VisitRouteStop
from src.session import Session

logger = logging.getLogger(__name__)

visit_routes_bp = Blueprint('visit_routes', __name__, url_prefix='/routes/visits')


@visit_routes_bp.route('/generate', methods=['POST'])
def generate_visit_route():
    """
    POST /routes/visits/generate
    
    Genera una ruta optimizada para que un vendedor visite múltiples clientes.
    
    Request Body:
    {
        "salesperson_id": 2,
        "salesperson_name": "Maria Gonzalez",  # opcional
        "salesperson_employee_id": "SALES-002",  # opcional
        "customer_ids": [1, 5, 12, 45, 67],
        "planned_date": "2025-11-20",
        "optimization_strategy": "minimize_distance",  # opcional (DEFAULT)
        "start_location": {  # opcional
            "name": "Oficina Central",
            "latitude": 4.6097,
            "longitude": -74.0817,
            "address": "Calle 100 #20-30"
        },
        "work_hours": {  # opcional
            "start": "08:00",
            "end": "18:00"
        },
        "service_time_per_visit_minutes": 30  # opcional (DEFAULT)
    }
    
    Estrategias de optimización:
    - 'minimize_distance': Minimiza distancia total (DEFAULT - RECOMENDADO)
    - 'minimize_time': Minimiza tiempo total de ruta
    - 'balanced': Balance entre distancia y tiempo
    
    Response Body (200 OK):
    {
        "status": "success",
        "route": {
            "id": 123,
            "route_code": "VISIT-20251120-S002-001",
            "salesperson": {
                "id": 2,
                "name": "Maria Gonzalez",
                "employee_id": "SALES-002"
            },
            "planned_date": "2025-11-20",
            "status": "draft",
            "metrics": {
                "total_stops": 5,
                "total_distance_km": 32.5,
                "estimated_duration_minutes": 195,
                "optimization_score": 92.3
            },
            "stops": [
                {
                    "sequence_order": 1,
                    "customer": {
                        "id": 12,
                        "name": "Farmacia San Rafael"
                    },
                    "location": {
                        "address": "Calle 50 #20-30",
                        "latitude": 4.6486259,
                        "longitude": -74.0628451
                    },
                    "estimated_times": {
                        "arrival": "2025-11-20T08:45:00",
                        "departure": "2025-11-20T09:15:00",
                        "service_minutes": 30
                    },
                    "distance_metrics": {
                        "from_previous_km": 5.2,
                        "travel_time_minutes": 15
                    }
                }
            ],
            "map_url": "https://maps.google.com/maps/dir/..."
        },
        "warnings": [],
        "computation_time_seconds": 2.35
    }
    
    Error Responses:
    - 400: Datos inválidos
    - 404: Vendedor o clientes no encontrados
    - 500: Error interno del servidor
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validar campos requeridos
        required_fields = ['salesperson_id', 'customer_ids', 'planned_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        salesperson_id = data['salesperson_id']
        customer_ids = data['customer_ids']
        planned_date_str = data['planned_date']
        
        # Validaciones
        if not isinstance(customer_ids, list) or not customer_ids:
            return jsonify({'error': 'customer_ids must be a non-empty array'}), 400
        
        if len(customer_ids) > 50:
            return jsonify({'error': 'Maximum 50 customers per route'}), 400
        
        # Parsear fecha
        try:
            planned_date = datetime.strptime(planned_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'planned_date must be in format YYYY-MM-DD'}), 400
        
        # Validar que no sea fecha pasada
        if planned_date < date.today():
            return jsonify({'error': 'planned_date cannot be in the past'}), 400
        
        # Parsear horario de trabajo
        work_hours = data.get('work_hours', {})
        try:
            work_start_str = work_hours.get('start', '08:00')
            work_end_str = work_hours.get('end', '18:00')
            work_start_time = datetime.strptime(work_start_str, '%H:%M').time()
            work_end_time = datetime.strptime(work_end_str, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'work_hours times must be in format HH:MM'}), 400
        
        # Obtener información del vendedor (opcional)
        salesperson_name = data.get('salesperson_name', f'Vendedor {salesperson_id}')
        salesperson_employee_id = data.get('salesperson_employee_id', f'SALES-{salesperson_id:03d}')
        
        # Crear comando
        command = GenerateVisitRoutesCommand(
            salesperson_id=salesperson_id,
            salesperson_name=salesperson_name,
            salesperson_employee_id=salesperson_employee_id,
            customer_ids=customer_ids,
            planned_date=planned_date,
            optimization_strategy=data.get('optimization_strategy', 'minimize_distance'),
            start_location=data.get('start_location'),
            end_location=data.get('end_location'),
            work_start_time=work_start_time,
            work_end_time=work_end_time,
            service_time_per_visit_minutes=data.get('service_time_per_visit_minutes', 30)
        )
        
        # Ejecutar
        logger.info(f"Generating visit route for salesperson {salesperson_id}")
        result = command.execute()
        
        if result['status'] == 'failed':
            return jsonify({
                'status': 'error',
                'errors': result['errors'],
                'warnings': result['warnings']
            }), 400
        
        route = result['route']
        
        return jsonify({
            'status': result['status'],
            'route': route.to_dict(include_stops=True),
            'warnings': result.get('warnings', []),
            'computation_time_seconds': result['computation_time_seconds']
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating visit route: {e}", exc_info=True)
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>', methods=['GET'])
def get_visit_route(route_id):
    """
    GET /routes/visits/{route_id}
    
    Obtiene detalle completo de una ruta de visitas.
    
    Response (200 OK):
    {
        "route": {
            "id": 123,
            "route_code": "VISIT-20251120-S002-001",
            ...
        }
    }
    
    Error Responses:
    - 404: Ruta no encontrada
    - 500: Error interno
    """
    try:
        route = VisitRoute.query.get(route_id)
        
        if not route:
            return jsonify({'error': f'Visit route {route_id} not found'}), 404
        
        return jsonify(route.to_dict(include_stops=True)), 200
        
    except Exception as e:
        logger.error(f"Error getting visit route: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/salesperson/<int:salesperson_id>', methods=['GET'])
def get_salesperson_routes(salesperson_id):
    """
    GET /routes/visits/salesperson/{salesperson_id}
    
    Obtiene todas las rutas de un vendedor.
    
    Query Parameters:
    - planned_date: Filtrar por fecha (YYYY-MM-DD)
    - status: Filtrar por estado (draft, confirmed, in_progress, completed, cancelled)
    - limit: Número máximo de resultados (default: 50)
    
    Response (200 OK):
    {
        "routes": [...],
        "total": 15
    }
    """
    try:
        # Parámetros de query
        planned_date_str = request.args.get('planned_date')
        status_str = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        # Construir query
        query = VisitRoute.query.filter_by(salesperson_id=salesperson_id)
        
        if planned_date_str:
            try:
                planned_date = datetime.strptime(planned_date_str, '%Y-%m-%d').date()
                query = query.filter_by(planned_date=planned_date)
            except ValueError:
                return jsonify({'error': 'planned_date must be in format YYYY-MM-DD'}), 400
        
        if status_str:
            try:
                status_enum = VisitRouteStatus(status_str)
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': f'Invalid status: {status_str}'}), 400
        
        # Ordenar por fecha descendente
        query = query.order_by(VisitRoute.planned_date.desc())
        
        # Limitar resultados
        routes = query.limit(limit).all()
        
        return jsonify({
            'routes': [route.to_dict(include_stops=False) for route in routes],
            'total': len(routes)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting salesperson routes: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>/confirm', methods=['PUT'])
def confirm_route(route_id):
    """
    PUT /routes/visits/{route_id}/confirm
    
    Confirma una ruta de visitas (cambia de draft a confirmed).
    
    Response (200 OK):
    {
        "message": "Route confirmed successfully",
        "route": {...}
    }
    
    Error Responses:
    - 404: Ruta no encontrada
    - 400: Estado inválido para confirmar
    - 500: Error interno
    """
    try:
        route = VisitRoute.query.get(route_id)
        
        if not route:
            return jsonify({'error': f'Visit route {route_id} not found'}), 404
        
        if route.status != VisitRouteStatus.DRAFT:
            return jsonify({'error': f'Cannot confirm route in status {route.status.value}'}), 400
        
        route.confirm()
        Session.commit()
        
        logger.info(f"Route {route.route_code} confirmed")
        
        return jsonify({
            'message': 'Route confirmed successfully',
            'route': route.to_dict(include_stops=True)
        }), 200
        
    except Exception as e:
        Session.rollback()
        logger.error(f"Error confirming route: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>/start', methods=['PUT'])
def start_route(route_id):
    """
    PUT /routes/visits/{route_id}/start
    
    Inicia una ruta de visitas (cambia de confirmed a in_progress).
    """
    try:
        route = VisitRoute.query.get(route_id)
        
        if not route:
            return jsonify({'error': f'Visit route {route_id} not found'}), 404
        
        route.start()
        Session.commit()
        
        logger.info(f"Route {route.route_code} started")
        
        return jsonify({
            'message': 'Route started successfully',
            'route': route.to_dict(include_stops=True)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        Session.rollback()
        logger.error(f"Error starting route: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>/complete', methods=['PUT'])
def complete_route(route_id):
    """
    PUT /routes/visits/{route_id}/complete
    
    Completa una ruta de visitas (cambia de in_progress a completed).
    """
    try:
        route = VisitRoute.query.get(route_id)
        
        if not route:
            return jsonify({'error': f'Visit route {route_id} not found'}), 404
        
        route.complete()
        Session.commit()
        
        logger.info(f"Route {route.route_code} completed")
        
        return jsonify({
            'message': 'Route completed successfully',
            'route': route.to_dict(include_stops=True)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        Session.rollback()
        logger.error(f"Error completing route: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>', methods=['DELETE'])
def cancel_route(route_id):
    """
    DELETE /routes/visits/{route_id}
    
    Cancela una ruta de visitas.
    
    Response (200 OK):
    {
        "message": "Route cancelled successfully"
    }
    """
    try:
        route = VisitRoute.query.get(route_id)
        
        if not route:
            return jsonify({'error': f'Visit route {route_id} not found'}), 404
        
        route.cancel()
        Session.commit()
        
        logger.info(f"Route {route.route_code} cancelled")
        
        return jsonify({
            'message': 'Route cancelled successfully',
            'route': route.to_dict(include_stops=False)
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        Session.rollback()
        logger.error(f"Error cancelling route: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>/stops/<int:stop_id>/complete', methods=['PUT'])
def complete_stop(route_id, stop_id):
    """
    PUT /routes/visits/{route_id}/stops/{stop_id}/complete
    
    Marca una parada como completada.
    
    Body (opcional):
    {
        "actual_arrival": "2025-11-20T09:00:00",
        "actual_departure": "2025-11-20T09:35:00",
        "notes": "Cliente satisfecho, interesado en nuevos productos"
    }
    """
    try:
        stop = VisitRouteStop.query.get(stop_id)
        
        if not stop or stop.route_id != route_id:
            return jsonify({'error': f'Stop {stop_id} not found in route {route_id}'}), 404
        
        data = request.get_json() or {}
        
        # Parsear tiempos reales
        actual_arrival = None
        actual_departure = None
        
        if 'actual_arrival' in data:
            try:
                actual_arrival = datetime.fromisoformat(data['actual_arrival'])
            except ValueError:
                return jsonify({'error': 'actual_arrival must be in ISO 8601 format'}), 400
        
        if 'actual_departure' in data:
            try:
                actual_departure = datetime.fromisoformat(data['actual_departure'])
            except ValueError:
                return jsonify({'error': 'actual_departure must be in ISO 8601 format'}), 400
        
        stop.complete(
            actual_arrival=actual_arrival,
            actual_departure=actual_departure,
            notes=data.get('notes')
        )
        
        Session.commit()
        
        logger.info(f"Stop {stop_id} completed in route {route_id}")
        
        return jsonify({
            'message': 'Stop completed successfully',
            'stop': stop.to_dict()
        }), 200
        
    except Exception as e:
        Session.rollback()
        logger.error(f"Error completing stop: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@visit_routes_bp.route('/<int:route_id>/stops/<int:stop_id>/skip', methods=['PUT'])
def skip_stop(route_id, stop_id):
    """
    PUT /routes/visits/{route_id}/stops/{stop_id}/skip
    
    Marca una parada como omitida.
    
    Body:
    {
        "reason": "Cliente cerrado temporalmente"
    }
    """
    try:
        stop = VisitRouteStop.query.get(stop_id)
        
        if not stop or stop.route_id != route_id:
            return jsonify({'error': f'Stop {stop_id} not found in route {route_id}'}), 404
        
        data = request.get_json()
        
        if not data or 'reason' not in data:
            return jsonify({'error': 'reason is required'}), 400
        
        stop.skip(reason=data['reason'])
        Session.commit()
        
        logger.info(f"Stop {stop_id} skipped in route {route_id}: {data['reason']}")
        
        return jsonify({
            'message': 'Stop skipped successfully',
            'stop': stop.to_dict()
        }), 200
        
    except Exception as e:
        Session.rollback()
        logger.error(f"Error skipping stop: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
