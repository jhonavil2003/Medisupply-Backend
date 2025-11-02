"""
Comandos para consultar y gestionar rutas de entrega.
"""

from typing import List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal
import logging

from src.models.delivery_route import DeliveryRoute
from src.models.route_stop import RouteStop
from src.models.route_assignment import RouteAssignment
from src.models.vehicle import Vehicle
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
    
    def __init__(self, route_id: int, include_stops: bool = True, include_assignments: bool = True):
        """
        Args:
            route_id: ID de la ruta
            include_stops: Incluir paradas en la respuesta
            include_assignments: Incluir asignaciones de pedidos
        """
        self.route_id = route_id
        self.include_stops = include_stops
        self.include_assignments = include_assignments
    
    def execute(self) -> Dict:
        """
        Obtiene detalle completo de la ruta.
        
        Returns:
            Dict con datos completos de la ruta
        """
        try:
            route = Session.query(DeliveryRoute).get(self.route_id)
            
            if not route:
                return {
                    'status': 'not_found',
                    'message': f'Ruta {self.route_id} no encontrada'
                }
            
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
