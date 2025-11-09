"""
Comandos para generación y gestión de rutas de entrega optimizadas.

Incluye:
- GenerateRoutesCommand: Comando unificado para generar rutas (recibe solo order_ids)
- CancelRoute: Comando para cancelar rutas
- UpdateRouteStatus: Comando para actualizar estados de rutas
"""

from typing import List, Dict, Optional
from datetime import datetime, date, time
import logging

from src.models.vehicle import Vehicle
from src.models.delivery_route import DeliveryRoute
from src.services.route_optimizer_service import RouteOptimizerService
from src.services.sales_service_client import get_sales_service_client
from src.session import Session

logger = logging.getLogger(__name__)


# =============================================================================
# COMANDO PRINCIPAL (MODERNO) - GenerateRoutesCommand
# =============================================================================

class GenerateRoutesCommand:
    """
    Comando unificado para generar rutas de entrega optimizadas.
    
    Este comando simplifica el proceso recibiendo solo IDs de órdenes y
    obteniendo automáticamente los detalles desde sales-service.
    
    Características:
    - Recibe solo order_ids (interfaz simple)
    - Obtiene detalles automáticamente desde sales-service
    - Valida estado de órdenes (confirmed, no ruteadas)
    - Response resumido y enfocado en valor
    - Integración completa con Google Maps API
    
    Flujo:
    1. Obtiene detalles de órdenes desde sales-service
    2. Valida que las órdenes estén confirmadas y no ruteadas
    3. Ejecuta optimización de rutas con OR-Tools
    4. Persiste rutas en base de datos
    5. Actualiza estado de órdenes en sales-service
    """
    
    def __init__(
        self,
        distribution_center_id: int,
        order_ids: List[int],
        planned_date: date,
        optimization_strategy: str = 'balanced',  # DEFAULT: Balancea múltiples objetivos
        force_regenerate: bool = False,
        created_by: str = 'system'
    ):
        """
        Inicializa el comando de generación de rutas.
        
        Args:
            distribution_center_id: ID del centro de distribución
            order_ids: Lista de IDs de órdenes a rutear
            planned_date: Fecha planeada de entrega
            optimization_strategy: Estrategia de optimización
                - 'balanced': Balance entre distancia, tiempo, capacidad y equidad (DEFAULT - RECOMENDADO)
                - 'minimize_distance': Minimiza distancia y consumo de gasolina
                - 'minimize_time': Prioriza tiempo de entrega
                - 'minimize_cost': Minimiza costo operativo total
                - 'priority_first': Entrega primero a clientes críticos
            force_regenerate: Si True, regenera rutas aunque ya existan
            created_by: Usuario que solicita la generación
        """
        self.distribution_center_id = distribution_center_id
        self.order_ids = order_ids if order_ids else []
        self.planned_date = planned_date
        self.optimization_strategy = optimization_strategy
        self.force_regenerate = force_regenerate
        self.created_by = created_by
        self.sales_client = get_sales_service_client()
    
    def execute(self) -> Dict:
        """
        Ejecuta la generación de rutas.
        
        Returns:
            Dict con resultado RESUMIDO:
            {
                'status': 'success' | 'partial' | 'failed' | 'no_orders' | ...,
                'summary': {
                    'routes_generated': int,
                    'orders_assigned': int,
                    'orders_unassigned': int,
                    'total_distance_km': float,
                    'estimated_duration_hours': float,
                    'optimization_score': float
                },
                'routes': [
                    {
                        'id': int,
                        'route_code': str,
                        'vehicle': {'id': int, 'plate': str, 'type': str},
                        'stops_count': int,
                        'orders_count': int,
                        'distance_km': float,
                        'duration_minutes': int,
                        'status': str
                    }
                ],
                'warnings': List[str],
                'errors': List[str],
                'computation_time_seconds': float
            }
        """
        start_time = datetime.now()
        errors = []
        warnings = []
        
        try:
            # PASO 1: Verificar conectividad con sales-service
            logger.info("🔍 Verificando conectividad con sales-service...")
            if not self.sales_client.health_check():
                logger.error("❌ Sales service no disponible")
                return self._build_error_response(
                    status='sales_service_unavailable',
                    message='No se pudo conectar con sales-service',
                    errors=['Sales service is down or unreachable'],
                    start_time=start_time
                )
            
            # PASO 2: Validar que se proporcionaron IDs de órdenes
            if not self.order_ids:
                logger.info("⚠️ No se proporcionaron IDs de órdenes")
                return self._build_error_response(
                    status='no_orders',
                    message='No se proporcionaron IDs de órdenes para rutear',
                    start_time=start_time
                )
            
            logger.info(f"📋 Solicitadas {len(self.order_ids)} órdenes para rutear")
            
            # PASO 3: Obtener detalles de órdenes desde sales-service
            logger.info("📡 Obteniendo detalles de órdenes desde sales-service...")
            batch_result = self.sales_client.get_orders_by_ids(self.order_ids)
            
            orders_data = batch_result.get('orders', [])
            not_found_ids = batch_result.get('not_found', [])
            
            if not_found_ids:
                warnings.append(f"{len(not_found_ids)} órdenes no encontradas: {not_found_ids}")
                logger.warning(f"⚠️ Órdenes no encontradas: {not_found_ids}")
            
            if not orders_data:
                logger.error("❌ Ninguna orden encontrada en sales-service")
                return self._build_error_response(
                    status='no_orders_found',
                    message='Ninguna de las órdenes solicitadas fue encontrada en sales-service',
                    errors=[f'Order IDs not found: {not_found_ids}'],
                    start_time=start_time
                )
            
            logger.info(f"✅ Obtenidas {len(orders_data)} órdenes desde sales-service")
            
            # PASO 4: Validar estado de las órdenes
            logger.info("🔍 Validando estado de órdenes...")
            valid_orders, validation_errors = self._validate_orders(orders_data)
            
            if validation_errors:
                warnings.extend(validation_errors)
                logger.warning(f"⚠️ {len(validation_errors)} órdenes con problemas de validación")
            
            if not valid_orders:
                logger.error("❌ Ninguna orden válida para rutear")
                return self._build_error_response(
                    status='no_valid_orders',
                    message='Ninguna orden cumple con los requisitos para ser ruteada',
                    errors=validation_errors,
                    start_time=start_time
                )
            
            logger.info(f"✅ {len(valid_orders)} órdenes válidas para rutear")
            
            # PASO 5: Verificar rutas existentes (si no es force_regenerate)
            if not self.force_regenerate:
                existing_routes_count = Session.query(DeliveryRoute).filter(
                    DeliveryRoute.distribution_center_id == self.distribution_center_id,
                    DeliveryRoute.planned_date == self.planned_date,
                    DeliveryRoute.status.in_(['draft', 'active', 'in_progress'])
                ).count()
                
                if existing_routes_count > 0:
                    logger.warning(
                        f"⚠️ Ya existen {existing_routes_count} rutas activas para "
                        f"DC {self.distribution_center_id} en {self.planned_date}"
                    )
                    return self._build_error_response(
                        status='existing_routes',
                        message=(
                            f'Ya existen {existing_routes_count} rutas activas para esta fecha. '
                            f'Use force_regenerate=true para regenerarlas.'
                        ),
                        start_time=start_time
                    )
            
            # PASO 6: Obtener vehículos disponibles
            logger.info("🚛 Obteniendo vehículos disponibles...")
            vehicles = Session.query(Vehicle).filter(
                Vehicle.home_distribution_center_id == self.distribution_center_id,
                Vehicle.is_available == True
            ).all()
            
            if not vehicles:
                logger.error(f"❌ No hay vehículos disponibles en DC {self.distribution_center_id}")
                return self._build_error_response(
                    status='no_vehicles',
                    message='No hay vehículos disponibles para generar rutas',
                    errors=['No available vehicles in distribution center'],
                    start_time=start_time
                )
            
            logger.info(f"✅ Encontrados {len(vehicles)} vehículos disponibles")
            
            # PASO 7: Transformar órdenes al formato esperado por RouteOptimizerService
            logger.info("🔄 Transformando datos de órdenes...")
            transformed_orders = self._transform_orders_for_optimizer(valid_orders)
            
            # PASO 8: Ejecutar optimización de rutas
            logger.info(
                f"🧮 Iniciando optimización de rutas: {len(transformed_orders)} órdenes, "
                f"{len(vehicles)} vehículos, estrategia: {self.optimization_strategy}"
            )
            
            optimization_result = RouteOptimizerService.optimize_routes(
                orders=transformed_orders,
                distribution_center_id=self.distribution_center_id,
                planned_date=self.planned_date,
                optimization_strategy=self.optimization_strategy,
                max_execution_time=30
            )
            
            if optimization_result['status'] == 'failed':
                logger.error(f"❌ Optimización de rutas falló: {optimization_result['errors']}")
                return self._build_error_response(
                    status='optimization_failed',
                    message='La optimización de rutas falló',
                    errors=optimization_result['errors'],
                    start_time=start_time
                )
            
            # PASO 9: Agregar metadata de creación a las rutas
            for route in optimization_result['routes']:
                route.created_by = self.created_by
            
            # PASO 10: Commit (RouteOptimizerService ya creó los objetos)
            Session.commit()
            logger.info("✅ Rutas guardadas en base de datos")
            
            # PASO 11: Actualizar estado de órdenes en sales-service
            if optimization_result['routes']:
                logger.info("📡 Actualizando estado de órdenes en sales-service...")
                self._update_orders_in_sales_service(optimization_result['routes'])
            
            # PASO 12: Construir response resumido
            computation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"✅ Generación completada: {len(optimization_result['routes'])} rutas, "
                f"{optimization_result['metrics'].get('total_orders_assigned', 0)} órdenes asignadas, "
                f"tiempo: {computation_time:.2f}s"
            )
            
            return self._build_success_response(
                routes=optimization_result['routes'],
                metrics=optimization_result['metrics'],
                unassigned_orders=optimization_result['unassigned_orders'],
                warnings=warnings,
                errors=errors,
                computation_time=computation_time
            )
        
        except Exception as e:
            Session.rollback()
            logger.exception(f"❌ Error inesperado en generación de rutas: {e}")
            return self._build_error_response(
                status='failed',
                message=f'Error inesperado: {str(e)}',
                errors=[str(e)],
                start_time=start_time
            )
    
    def _validate_orders(self, orders: List[Dict]) -> tuple:
        """
        Valida que las órdenes cumplan con los requisitos para ser ruteadas.
        
        Validaciones:
        - Estado debe ser 'confirmed'
        - No debe estar ya ruteada (is_routed = false)
        - Debe tener dirección de entrega
        - Debe tener coordenadas o capacidad de geocoding
        
        Args:
            orders: Lista de órdenes desde sales-service
        
        Returns:
            Tupla (órdenes_válidas, errores_validación)
        """
        valid_orders = []
        validation_errors = []
        
        for order in orders:
            order_id = order.get('id')
            order_number = order.get('order_number', f'Order-{order_id}')
            
            # Validar estado
            if order.get('status') != 'confirmed':
                validation_errors.append(
                    f"Orden {order_number}: Estado '{order.get('status')}' no es 'confirmed'"
                )
                continue
            
            # Validar que no esté ya ruteada
            if order.get('is_routed', False):
                validation_errors.append(
                    f"Orden {order_number}: Ya está asignada a una ruta"
                )
                continue
            
            # Validar dirección
            delivery_address = order.get('delivery_address', '').strip()
            if not delivery_address or len(delivery_address) < 10:
                validation_errors.append(
                    f"Orden {order_number}: Dirección de entrega inválida o incompleta"
                )
                continue
            
            # Agregar a órdenes válidas
            valid_orders.append(order)
        
        return valid_orders, validation_errors
    
    def _transform_orders_for_optimizer(self, orders: List[Dict]) -> List[Dict]:
        """
        Transforma órdenes del formato de sales-service al formato esperado
        por RouteOptimizerService.
        
        Args:
            orders: Órdenes desde sales-service
        
        Returns:
            Lista de órdenes en formato para RouteOptimizerService
        """
        transformed = []
        
        for order in orders:
            # Calcular peso y volumen total desde items
            total_weight_kg = 0.0
            total_volume_m3 = 0.0
            requires_cold_chain = False
            
            for item in order.get('items', []):
                total_weight_kg += float(item.get('weight_kg', 0) * item.get('quantity', 1))
                total_volume_m3 += float(item.get('volume_m3', 0) * item.get('quantity', 1))
                
                if item.get('requires_cold_chain', False):
                    requires_cold_chain = True
            
            transformed_order = {
                'id': order['id'],
                'order_number': order['order_number'],
                'customer_id': order['customer_id'],
                'customer_name': order.get('customer_name') or order.get('customer', {}).get('razon_social', 'Desconocido'),
                'delivery_address': order['delivery_address'],
                'city': order.get('delivery_city', ''),
                'department': order.get('delivery_department', ''),
                'latitude': order.get('delivery_latitude'),
                'longitude': order.get('delivery_longitude'),
                'weight_kg': total_weight_kg if total_weight_kg > 0 else order.get('estimated_weight_kg', 10.0),
                'volume_m3': total_volume_m3 if total_volume_m3 > 0 else order.get('estimated_volume_m3', 0.1),
                'requires_cold_chain': requires_cold_chain,
                'clinical_priority': order.get('clinical_priority', 3),
                'time_window_start': order.get('delivery_time_window_start'),
                'time_window_end': order.get('delivery_time_window_end'),
                'service_time_minutes': 15  # Default
            }
            
            transformed.append(transformed_order)
        
        return transformed
    
    def _update_orders_in_sales_service(self, routes: List[DeliveryRoute]):
        """
        Actualiza el estado de las órdenes asignadas en sales-service.
        
        Args:
            routes: Lista de rutas generadas
        """
        updated_count = 0
        failed_count = 0
        
        for route in routes:
            # Obtener todas las asignaciones de la ruta
            assignments = route.assignments.all()
            
            for assignment in assignments:
                order_id = assignment.order_id
                
                try:
                    # Actualizar estado a 'processing'
                    success = self.sales_client.update_order_status(
                        order_id=order_id,
                        new_status='processing',
                        notes=f'Asignado a ruta {route.route_code}'
                    )
                    
                    if success:
                        # Marcar como ruteado
                        self.sales_client._make_request(
                            'PUT',
                            f'/orders/{order_id}',
                            json_data={
                                'is_routed': True,
                                'route_id': route.id,
                                'routed_at': datetime.utcnow().isoformat()
                            }
                        )
                        updated_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ No se pudo actualizar orden {order_id}")
                
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Error actualizando orden {order_id}: {e}")
        
        logger.info(
            f"📡 Órdenes actualizadas en sales-service: {updated_count} exitosas, "
            f"{failed_count} fallidas"
        )
    
    def _build_success_response(
        self,
        routes: List[DeliveryRoute],
        metrics: Dict,
        unassigned_orders: List[Dict],
        warnings: List[str],
        errors: List[str],
        computation_time: float
    ) -> Dict:
        """
        Construye response resumido de éxito.
        """
        status = 'success' if not unassigned_orders else 'partial'
        
        # Calcular totales
        total_distance_km = sum(float(r.total_distance_km or 0) for r in routes)
        total_duration_minutes = sum(r.estimated_duration_minutes or 0 for r in routes)
        avg_optimization_score = (
            sum(float(r.optimization_score or 0) for r in routes) / len(routes)
            if routes else 0
        )
        
        return {
            'status': status,
            'summary': {
                'routes_generated': len(routes),
                'orders_assigned': metrics.get('total_orders_assigned', 0),
                'orders_unassigned': len(unassigned_orders),
                'total_distance_km': round(total_distance_km, 2),
                'estimated_duration_hours': round(total_duration_minutes / 60, 1),
                'optimization_score': round(avg_optimization_score, 1)
            },
            'routes': [
                {
                    'id': r.id,
                    'route_code': r.route_code,
                    'vehicle': {
                        'id': r.vehicle.id,
                        'plate': r.vehicle.plate,
                        'type': r.vehicle.vehicle_type
                    },
                    'stops_count': r.total_stops,
                    'orders_count': r.total_orders,
                    'distance_km': float(r.total_distance_km or 0),
                    'duration_minutes': r.estimated_duration_minutes,
                    'status': r.status
                }
                for r in routes
            ],
            'warnings': warnings,
            'errors': errors,
            'computation_time_seconds': round(computation_time, 2)
        }
    
    def _build_error_response(
        self,
        status: str,
        message: str,
        errors: Optional[List[str]] = None,
        start_time: Optional[datetime] = None
    ) -> Dict:
        """
        Construye response de error estandarizado.
        """
        computation_time = (
            (datetime.now() - start_time).total_seconds()
            if start_time else 0
        )
        
        return {
            'status': status,
            'summary': {
                'routes_generated': 0,
                'orders_assigned': 0,
                'orders_unassigned': len(self.order_ids),
                'total_distance_km': 0.0,
                'estimated_duration_hours': 0.0,
                'optimization_score': 0.0
            },
            'routes': [],
            'warnings': [],
            'errors': errors or [message],
            'computation_time_seconds': round(computation_time, 2),
            'message': message
        }


# =============================================================================
# COMANDOS AUXILIARES
# =============================================================================


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
