"""
Comandos para consultar y gestionar rutas de entrega.
"""

from typing import Optional, Dict
from datetime import date
import logging

from src.models.delivery_route import DeliveryRoute
from src.session import Session

logger = logging.getLogger(__name__)


class GetRoutes:
    """
    Comando para consultar rutas con filtros.
    """
    
    def __init__(
        self,
        distribution_center_id: Optional[int] = None,
        planned_date: Optional[date] = None,
        status: Optional[str] = None,
        vehicle_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ):
        """
        Args:
            distribution_center_id: Filtrar por centro de distribución
            planned_date: Filtrar por fecha planeada
            status: Filtrar por estado (draft, active, in_progress, completed, cancelled)
            vehicle_id: Filtrar por vehículo
            limit: Límite de resultados
            offset: Offset para paginación
        """
        self.distribution_center_id = distribution_center_id
        self.planned_date = planned_date
        self.status = status
        self.vehicle_id = vehicle_id
        self.limit = limit
        self.offset = offset
    
    def execute(self) -> Dict:
        """
        Ejecuta la consulta de rutas.
        
        Returns:
            Dict con resultados paginados
        """
        try:
            query = Session.query(DeliveryRoute)
            
            # Aplicar filtros
            if self.distribution_center_id:
                query = query.filter(
                    DeliveryRoute.distribution_center_id == self.distribution_center_id
                )
            
            if self.planned_date:
                query = query.filter(DeliveryRoute.planned_date == self.planned_date)
            
            if self.status:
                query = query.filter(DeliveryRoute.status == self.status)
            
            if self.vehicle_id:
                query = query.filter(DeliveryRoute.vehicle_id == self.vehicle_id)
            
            # Ordenar por fecha planeada (más recientes primero)
            query = query.order_by(DeliveryRoute.planned_date.desc(), DeliveryRoute.id.desc())
            
            # Contar total
            total = query.count()
            
            # Aplicar paginación
            routes = query.limit(self.limit).offset(self.offset).all()
            
            # Serializar
            routes_data = [route.to_dict(include_vehicle=True) for route in routes]
            
            return {
                'status': 'success',
                'routes': routes_data,
                'total': total,
                'limit': self.limit,
                'offset': self.offset,
                'has_more': (self.offset + len(routes)) < total
            }
        
        except Exception as e:
            logger.exception(f"Error consultando rutas: {e}")
            return {
                'status': 'error',
                'message': f'Error al consultar rutas: {str(e)}',
                'routes': [],
                'total': 0
            }


class GetRouteById:
    """
    Comando para obtener detalle completo de una ruta.
    """
    
    def __init__(
        self, 
        route_id: int, 
        include_stops: bool = True, 
        include_assignments: bool = True,
        summary_mode: bool = False
    ):
        """
        Args:
            route_id: ID de la ruta
            include_stops: Incluir paradas en la respuesta
            include_assignments: Incluir asignaciones de pedidos
            summary_mode: Si True, retorna solo información esencial (modo resumido)
        """
        self.route_id = route_id
        self.include_stops = include_stops
        self.include_assignments = include_assignments
        self.summary_mode = summary_mode
    
    def execute(self) -> Dict:
        """
        Obtiene detalle completo de la ruta.
        
        Returns:
            Dict con datos completos de la ruta (o resumidos si summary_mode=True)
        """
        try:
            route = Session.query(DeliveryRoute).get(self.route_id)
            
            if not route:
                return {
                    'status': 'not_found',
                    'message': f'Ruta {self.route_id} no encontrada'
                }
            
            if self.summary_mode:
                # Modo resumido - solo lo esencial
                route_data = self._build_summary(route)
            else:
                # Modo completo
                route_data = route.to_dict(
                    include_stops=self.include_stops,
                    include_vehicle=True,
                    include_assignments=self.include_assignments
                )
            
            return {
                'status': 'success',
                'route': route_data
            }
        
        except Exception as e:
            logger.exception(f"Error obteniendo ruta {self.route_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error al obtener ruta: {str(e)}'
            }
    
    def _build_summary(self, route: DeliveryRoute) -> Dict:
        """
        Construye un resumen compacto de la ruta con solo información esencial.
        """
        # Obtener paradas ordenadas
        stops = sorted(route.stops, key=lambda s: s.sequence_order)
        
        # Filtrar solo paradas de entrega (excluir depot y return)
        delivery_stops = [s for s in stops if s.stop_type == 'delivery']
        
        # Obtener todas las asignaciones (ejecutar la query lazy)
        all_assignments = list(route.assignments)
        
        # Construir lista de paradas resumidas
        stops_summary = []
        for stop in delivery_stops:
            # Obtener asignaciones de esta parada
            stop_assignments = [a for a in all_assignments if a.stop_id == stop.id]
            
            stop_info = {
                'sequence': stop.sequence_order,
                'customer_name': stop.customer_name or 'Desconocido',
                'address': stop.delivery_address or 'Sin dirección',
                'city': stop.city,
                'coordinates': {
                    'lat': float(stop.latitude) if stop.latitude else None,
                    'lng': float(stop.longitude) if stop.longitude else None
                },
                'estimated_arrival': stop.estimated_arrival_time.isoformat() if stop.estimated_arrival_time else None,
                'orders': [
                    {
                        'order_id': assignment.order_id,
                        'order_number': assignment.order_number,
                        'customer_name': assignment.customer_name or stop.customer_name or 'Desconocido',
                        'clinical_priority': assignment.clinical_priority,
                        'requires_cold_chain': assignment.requires_cold_chain
                    }
                    for assignment in stop_assignments
                ],
                'status': stop.status
            }
            stops_summary.append(stop_info)
        
        # Construir respuesta resumida
        return {
            'id': route.id,
            'route_code': route.route_code,
            'status': route.status,
            'planned_date': route.planned_date.isoformat() if route.planned_date else None,
            'distribution_center_id': route.distribution_center_id,
            
            # Vehículo
            'vehicle': {
                'id': route.vehicle.id if route.vehicle else None,
                'plate': route.vehicle.plate if route.vehicle else None,
                'type': route.vehicle.vehicle_type if route.vehicle else None,
                'driver': route.vehicle.driver_name if route.vehicle else None
            } if route.vehicle else None,
            
            # Métricas
            'metrics': {
                'total_stops': len(delivery_stops),
                'total_orders': len(all_assignments),
                'total_distance_km': float(route.total_distance_km) if route.total_distance_km else 0.0,
                'estimated_duration_minutes': route.estimated_duration_minutes
            },
            
            # Paradas
            'stops': stops_summary,
            
            # Tiempos
            'schedule': {
                'start_time': route.estimated_start_time.isoformat() if route.estimated_start_time else None,
                'end_time': route.estimated_end_time.isoformat() if route.estimated_end_time else None
            },
            
            # Optimización
            'optimization_score': float(route.optimization_score) if route.optimization_score else None,
            
            # Metadata
            'created_at': route.created_at.isoformat() if route.created_at else None,
            'created_by': route.created_by
        }


class GetRoutesByDate:
    """
    Comando para obtener todas las rutas de una fecha específica.
    """
    
    def __init__(self, distribution_center_id: int, planned_date: date):
        self.distribution_center_id = distribution_center_id
        self.planned_date = planned_date
    
    def execute(self) -> Dict:
        """
        Obtiene rutas de una fecha con métricas resumidas.
        """
        try:
            routes = Session.query(DeliveryRoute).filter(
                DeliveryRoute.distribution_center_id == self.distribution_center_id,
                DeliveryRoute.planned_date == self.planned_date
            ).all()
            
            # Calcular métricas agregadas
            total_routes = len(routes)
            total_distance = sum(float(r.total_distance_km) for r in routes)
            total_orders = sum(r.total_orders for r in routes)
            
            status_counts = {}
            for route in routes:
                status_counts[route.status] = status_counts.get(route.status, 0) + 1
            
            routes_data = [route.to_dict(include_vehicle=True) for route in routes]
            
            return {
                'status': 'success',
                'date': self.planned_date.isoformat(),
                'distribution_center_id': self.distribution_center_id,
                'routes': routes_data,
                'summary': {
                    'total_routes': total_routes,
                    'total_distance_km': round(total_distance, 2),
                    'total_orders': total_orders,
                    'status_counts': status_counts
                }
            }
        
        except Exception as e:
            logger.exception(f"Error obteniendo rutas por fecha: {e}")
            return {
                'status': 'error',
                'message': f'Error al obtener rutas: {str(e)}'
            }
