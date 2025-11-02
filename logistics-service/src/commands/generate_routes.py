"""
Comando para generar rutas de entrega optimizadas.

Este comando orquesta la generación de rutas desde pedidos confirmados,
integrándose con sales-service y utilizando el RouteOptimizerService.
"""

from typing import List, Optional, Dict
from datetime import datetime, date, time
import logging

from src.models.vehicle import Vehicle
from src.models.delivery_route import DeliveryRoute
from src.services.route_optimizer_service import RouteOptimizerService
from src.session import Session

logger = logging.getLogger(__name__)


def _serialize_order_for_json(order: Dict) -> Dict:
    """
    Serializa un pedido para que sea compatible con JSON.
    Convierte objetos datetime.time a strings.
    """
    serialized = order.copy()
    
    # Convertir time_window_start/end si existen
    if isinstance(serialized.get('time_window_start'), time):
        serialized['time_window_start'] = serialized['time_window_start'].isoformat()
    
    if isinstance(serialized.get('time_window_end'), time):
        serialized['time_window_end'] = serialized['time_window_end'].isoformat()
    
    return serialized


class GenerateRoutes:
    """
    Comando para generar rutas de entrega optimizadas.
    """
    
    def __init__(
        self,
        distribution_center_id: int,
        planned_date: date,
        orders: List[Dict],
        optimization_strategy: str = 'balanced',
        force_regenerate: bool = False,
        created_by: str = 'system'
    ):
        """
        Inicializa el comando de generación de rutas.
        
        Args:
            distribution_center_id: ID del centro de distribución
            planned_date: Fecha planeada de entrega
            orders: Lista de pedidos a rutear (estructura completa)
            optimization_strategy: Estrategia de optimización
                - 'balanced': Balance entre costo, tiempo y prioridades
                - 'minimize_time': Prioriza tiempo de entrega
                - 'minimize_distance': Minimiza distancia recorrida
                - 'minimize_cost': Minimiza costo operativo
                - 'priority_first': Entrega primero a clientes críticos
            force_regenerate: Si True, regenera rutas aunque ya existan
            created_by: Usuario que solicita la generación
        """
        self.distribution_center_id = distribution_center_id
        self.planned_date = planned_date
        self.orders = orders
        self.optimization_strategy = optimization_strategy
        self.force_regenerate = force_regenerate
        self.created_by = created_by
    
    def execute(self) -> Dict:
        """
        Ejecuta la generación de rutas.
        
        Flujo:
        1. Validar que no existan rutas activas para la fecha (si no es force_regenerate)
        2. Validar que hay pedidos para rutear
        3. Obtener vehículos disponibles
        4. Ejecutar optimización con RouteOptimizerService
        5. Guardar rutas en BD
        6. Retornar resultado
        
        Returns:
            Dict con resultado:
            {
                'status': 'success' | 'no_orders' | 'no_vehicles' | 'failed',
                'message': str,
                'routes_generated': int,
                'total_orders_assigned': int,
                'total_orders_unassigned': int,
                'computation_time_seconds': float,
                'routes': List[Dict],  # Serialización de rutas
                'unassigned_orders': List[Dict],
                'metrics': Dict,
                'errors': List[str]
            }
        """
        start_time = datetime.now()
        
        try:
            # 1. Verificar rutas existentes
            if not self.force_regenerate:
                existing_routes = Session.query(DeliveryRoute).filter(
                    DeliveryRoute.distribution_center_id == self.distribution_center_id,
                    DeliveryRoute.planned_date == self.planned_date,
                    DeliveryRoute.status.in_(['draft', 'active', 'in_progress'])
                ).count()
                
                if existing_routes > 0:
                    logger.warning(
                        f"Ya existen {existing_routes} rutas activas para "
                        f"DC {self.distribution_center_id} en {self.planned_date}"
                    )
                    return {
                        'status': 'existing_routes',
                        'message': (
                            f'Ya existen {existing_routes} rutas activas para esta fecha. '
                            f'Use force_regenerate=true para regenerarlas.'
                        ),
                        'routes_generated': 0,
                        'total_orders_assigned': 0,
                        'total_orders_unassigned': len(self.orders),
                        'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                        'routes': [],
                        'unassigned_orders': [_serialize_order_for_json(order) for order in self.orders],
                        'metrics': {},
                        'errors': []
                    }
            
            # 2. Validar pedidos
            if not self.orders:
                logger.info("No hay pedidos para rutear")
                return {
                    'status': 'no_orders',
                    'message': 'No hay pedidos para rutear',
                    'routes_generated': 0,
                    'total_orders_assigned': 0,
                    'total_orders_unassigned': 0,
                    'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'routes': [],
                    'unassigned_orders': [],
                    'metrics': {},
                    'errors': []
                }
            
            # 3. Obtener vehículos disponibles
            vehicles = Session.query(Vehicle).filter(
                Vehicle.home_distribution_center_id == self.distribution_center_id,
                Vehicle.is_available == True
            ).all()
            
            if not vehicles:
                logger.error(f"No hay vehículos disponibles en DC {self.distribution_center_id}")
                return {
                    'status': 'no_vehicles',
                    'message': 'No hay vehículos disponibles para generar rutas',
                    'routes_generated': 0,
                    'total_orders_assigned': 0,
                    'total_orders_unassigned': len(self.orders),
                    'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'routes': [],
                    'unassigned_orders': [_serialize_order_for_json(order) for order in self.orders],
                    'metrics': {},
                    'errors': ['No hay vehículos disponibles']
                }
            
            logger.info(
                f"Iniciando generación de rutas: {len(self.orders)} pedidos, "
                f"{len(vehicles)} vehículos, estrategia: {self.optimization_strategy}"
            )
            
            # 4. Ejecutar optimización
            result = RouteOptimizerService.optimize_routes(
                orders=self.orders,
                distribution_center_id=self.distribution_center_id,
                planned_date=self.planned_date,
                optimization_strategy=self.optimization_strategy,
                max_execution_time=30
            )
            
            if result['status'] == 'failed':
                logger.error(f"Optimización de rutas falló: {result['errors']}")
                return {
                    'status': 'failed',
                    'message': 'Error al optimizar rutas',
                    'routes_generated': 0,
                    'total_orders_assigned': 0,
                    'total_orders_unassigned': len(self.orders),
                    'computation_time_seconds': result['computation_time_seconds'],
                    'routes': [],
                    'unassigned_orders': [_serialize_order_for_json(order) for order in self.orders],
                    'metrics': {},
                    'errors': result['errors']
                }
            
            # 5. Agregar información de creación a las rutas
            for route in result['routes']:
                route.created_by = self.created_by
            
            # 6. Commit (RouteOptimizerService ya creó los objetos)
            Session.commit()
            
            # 7. Serializar rutas para respuesta
            routes_data = [
                route.to_dict(include_stops=True, include_vehicle=True, include_assignments=True)
                for route in result['routes']
            ]
            
            computation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Generación completada: {len(result['routes'])} rutas, "
                f"{result['metrics'].get('total_orders_assigned', 0)} pedidos asignados, "
                f"tiempo: {computation_time:.2f}s"
            )
            
            return {
                'status': result['status'],  # 'success' o 'partial'
                'message': self._get_success_message(result),
                'routes_generated': len(result['routes']),
                'total_orders_assigned': result['metrics'].get('total_orders_assigned', 0),
                'total_orders_unassigned': len(result['unassigned_orders']),
                'computation_time_seconds': computation_time,
                'routes': routes_data,
                'unassigned_orders': [_serialize_order_for_json(order) for order in result['unassigned_orders']],
                'metrics': result['metrics'],
                'errors': result['errors']
            }
        
        except Exception as e:
            Session.rollback()
            logger.exception(f"Error inesperado en generación de rutas: {e}")
            return {
                'status': 'failed',
                'message': f'Error inesperado: {str(e)}',
                'routes_generated': 0,
                'total_orders_assigned': 0,
                'total_orders_unassigned': len(self.orders),
                'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                'routes': [],
                'unassigned_orders': [_serialize_order_for_json(order) for order in self.orders],
                'metrics': {},
                'errors': [str(e)]
            }
    
    def _get_success_message(self, result: Dict) -> str:
        """Genera mensaje de éxito descriptivo."""
        routes_count = len(result['routes'])
        assigned = result['metrics'].get('total_orders_assigned', 0)
        unassigned = len(result['unassigned_orders'])
        
        if result['status'] == 'success':
            return (
                f"Se generaron {routes_count} ruta(s) optimizada(s) con "
                f"{assigned} pedido(s) asignado(s)"
            )
        else:  # partial
            return (
                f"Se generaron {routes_count} ruta(s) con {assigned} pedido(s) asignado(s). "
                f"{unassigned} pedido(s) no pudieron ser asignados"
            )


class CancelRoute:
    """
    Comando para cancelar una ruta existente.
    """
    
    def __init__(self, route_id: int, reason: str, cancelled_by: str):
        """
        Args:
            route_id: ID de la ruta a cancelar
            reason: Motivo de cancelación
            cancelled_by: Usuario que cancela
        """
        self.route_id = route_id
        self.reason = reason
        self.cancelled_by = cancelled_by
    
    def execute(self) -> Dict:
        """
        Cancela una ruta y libera los pedidos asignados.
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            route = Session.query(DeliveryRoute).get(self.route_id)
            
            if not route:
                return {
                    'status': 'error',
                    'message': f'Ruta {self.route_id} no encontrada'
                }
            
            if route.status == 'completed':
                return {
                    'status': 'error',
                    'message': 'No se puede cancelar una ruta completada'
                }
            
            if route.status == 'cancelled':
                return {
                    'status': 'warning',
                    'message': 'La ruta ya estaba cancelada'
                }
            
            # Actualizar estado
            route.status = 'cancelled'
            route.notes = f"{route.notes or ''}\n\nCANCELADA por {self.cancelled_by}: {self.reason}"
            route.updated_at = datetime.now()
            
            Session.commit()
            
            logger.info(f"Ruta {route.route_code} cancelada por {self.cancelled_by}: {self.reason}")
            
            return {
                'status': 'success',
                'message': f'Ruta {route.route_code} cancelada exitosamente',
                'route': route.to_dict()
            }
        
        except Exception as e:
            Session.rollback()
            logger.exception(f"Error cancelando ruta {self.route_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error al cancelar ruta: {str(e)}'
            }


class UpdateRouteStatus:
    """
    Comando para actualizar el estado de una ruta.
    """
    
    def __init__(self, route_id: int, new_status: str, updated_by: str):
        """
        Args:
            route_id: ID de la ruta
            new_status: Nuevo estado (active, in_progress, completed)
            updated_by: Usuario que actualiza
        """
        self.route_id = route_id
        self.new_status = new_status
        self.updated_by = updated_by
    
    def execute(self) -> Dict:
        """
        Actualiza el estado de la ruta.
        
        Transiciones válidas:
        - draft → active
        - active → in_progress
        - in_progress → completed
        - * → cancelled (con CancelRoute)
        """
        try:
            route = Session.query(DeliveryRoute).get(self.route_id)
            
            if not route:
                return {
                    'status': 'error',
                    'message': f'Ruta {self.route_id} no encontrada'
                }
            
            # Validar transición
            valid_transitions = {
                'draft': ['active'],
                'active': ['in_progress'],
                'in_progress': ['completed'],
                'completed': [],
                'cancelled': []
            }
            
            if self.new_status not in valid_transitions.get(route.status, []):
                return {
                    'status': 'error',
                    'message': (
                        f'Transición inválida: {route.status} → {self.new_status}. '
                        f'Transiciones válidas: {valid_transitions.get(route.status, [])}'
                    )
                }
            
            # Actualizar estado y tiempos
            old_status = route.status
            route.status = self.new_status
            route.updated_at = datetime.now()
            
            if self.new_status == 'in_progress' and not route.actual_start_time:
                route.actual_start_time = datetime.now()
            
            if self.new_status == 'completed' and not route.actual_end_time:
                route.actual_end_time = datetime.now()
            
            Session.commit()
            
            logger.info(
                f"Ruta {route.route_code} actualizada: {old_status} → {self.new_status} "
                f"por {self.updated_by}"
            )
            
            return {
                'status': 'success',
                'message': f'Estado de ruta actualizado a {self.new_status}',
                'route': route.to_dict()
            }
        
        except Exception as e:
            Session.rollback()
            logger.exception(f"Error actualizando estado de ruta {self.route_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error al actualizar estado: {str(e)}'
            }
