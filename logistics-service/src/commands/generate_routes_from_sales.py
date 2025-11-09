"""
Comando para generar rutas obteniendo pedidos automáticamente desde sales-service.

Este comando extiende GenerateRoutes integrando la comunicación con sales-service
para obtener pedidos confirmados pendientes de rutear.
"""

from typing import Optional, Dict, List
from datetime import date, datetime
import logging

from src.commands.generate_routes import GenerateRoutesCommand
from src.services.sales_service_client import get_sales_service_client
from src.session import Session

logger = logging.getLogger(__name__)


class GenerateRoutesFromSalesService:
    """
    Comando que genera rutas obteniendo pedidos automáticamente desde sales-service.
    
    Flujo:
    1. Consultar sales-service para obtener pedidos confirmados
    2. Filtrar pedidos sin asignar a ruta
    3. Validar datos necesarios (direcciones, prioridades, etc.)
    4. Ejecutar GenerateRoutes con los pedidos obtenidos
    5. Actualizar estado de pedidos en sales-service
    """
    
    def __init__(
        self,
        distribution_center_id: int,
        planned_date: date,
        optimization_strategy: str = 'balanced',
        force_regenerate: bool = False,
        created_by: str = 'system',
        max_orders: Optional[int] = None
    ):
        """
        Inicializa el comando.
        
        Args:
            distribution_center_id: ID del centro de distribución
            planned_date: Fecha planeada de entrega
            optimization_strategy: Estrategia de optimización
            force_regenerate: Si True, regenera rutas aunque ya existan
            created_by: Usuario que solicita la generación
            max_orders: Límite máximo de pedidos a procesar (para testing)
        """
        self.distribution_center_id = distribution_center_id
        self.planned_date = planned_date
        self.optimization_strategy = optimization_strategy
        self.force_regenerate = force_regenerate
        self.created_by = created_by
        self.max_orders = max_orders
        self.sales_client = get_sales_service_client()
    
    def execute(self) -> Dict:
        """
        Ejecuta la generación de rutas con auto-fetch de pedidos.
        
        Returns:
            Dict con resultado completo incluyendo:
            - Resultado de generación de rutas
            - Estadísticas de pedidos obtenidos
            - Pedidos actualizados en sales-service
            - Errores de comunicación con sales-service
        """
        start_time = datetime.now()
        result = {
            'status': 'failed',
            'message': '',
            'routes_generated': 0,
            'total_orders_assigned': 0,
            'total_orders_unassigned': 0,
            'computation_time_seconds': 0.0,
            'routes': [],
            'unassigned_orders': [],
            'metrics': {},
            'errors': [],
            'sales_service_integration': {
                'orders_fetched': 0,
                'orders_valid': 0,
                'orders_invalid': 0,
                'orders_updated': 0,
                'communication_errors': []
            }
        }
        
        try:
            # 1. Verificar conectividad con sales-service
            logger.info("Verificando conectividad con sales-service...")
            if not self.sales_client.health_check():
                logger.error("Sales service no disponible")
                result['status'] = 'sales_service_unavailable'
                result['message'] = (
                    'No se pudo conectar con sales-service. '
                    'El circuito está abierto o el servicio no responde.'
                )
                result['errors'].append('Sales service unavailable')
                result['computation_time_seconds'] = (datetime.now() - start_time).total_seconds()
                return result
            
            # 2. Obtener pedidos confirmados desde sales-service
            logger.info(
                f"Obteniendo pedidos confirmados para DC {self.distribution_center_id} "
                f"y fecha {self.planned_date}"
            )
            
            orders = self.sales_client.get_confirmed_orders(
                distribution_center_id=self.distribution_center_id,
                planned_date=self.planned_date,
                unrouted_only=True,
                limit=self.max_orders
            )
            
            result['sales_service_integration']['orders_fetched'] = len(orders)
            
            if not orders:
                logger.info("No hay pedidos confirmados pendientes de rutear")
                result['status'] = 'no_orders'
                result['message'] = (
                    'No hay pedidos confirmados pendientes de rutear para '
                    f'DC {self.distribution_center_id} en {self.planned_date}'
                )
                result['computation_time_seconds'] = (datetime.now() - start_time).total_seconds()
                return result
            
            logger.info(f"Obtenidos {len(orders)} pedidos desde sales-service")
            
            # 3. Validar y transformar pedidos
            valid_orders, invalid_orders = self._validate_orders(orders)
            
            result['sales_service_integration']['orders_valid'] = len(valid_orders)
            result['sales_service_integration']['orders_invalid'] = len(invalid_orders)
            
            if invalid_orders:
                logger.warning(f"Se encontraron {len(invalid_orders)} pedidos inválidos")
                for order in invalid_orders:
                    result['errors'].append(
                        f"Pedido {order.get('order_number')} inválido: {order.get('validation_error')}"
                    )
            
            if not valid_orders:
                logger.error("No hay pedidos válidos para rutear")
                result['status'] = 'no_valid_orders'
                result['message'] = 'Todos los pedidos tienen errores de validación'
                result['computation_time_seconds'] = (datetime.now() - start_time).total_seconds()
                return result
            
            # 4. Ejecutar generación de rutas
            logger.info(f"Generando rutas para {len(valid_orders)} pedidos válidos")
            
            generate_command = GenerateRoutesCommand(
                distribution_center_id=self.distribution_center_id,
                planned_date=self.planned_date,
                orders=valid_orders,
                optimization_strategy=self.optimization_strategy,
                force_regenerate=self.force_regenerate,
                created_by=self.created_by
            )
            
            route_result = generate_command.execute()
            
            # Copiar resultado de generación de rutas
            result['status'] = route_result.get('status')
            result['message'] = route_result.get('message')
            result['routes_generated'] = route_result.get('routes_generated', 0)
            result['total_orders_assigned'] = route_result.get('total_orders_assigned', 0)
            result['total_orders_unassigned'] = route_result.get('total_orders_unassigned', 0)
            result['routes'] = route_result.get('routes', [])
            result['unassigned_orders'] = route_result.get('unassigned_orders', [])
            result['metrics'] = route_result.get('metrics', {})
            result['errors'].extend(route_result.get('errors', []))
            
            # 5. Actualizar estado de pedidos en sales-service
            if route_result.get('status') == 'success' and result['routes_generated'] > 0:
                logger.info("Actualizando estado de pedidos en sales-service")
                self._update_orders_in_sales_service(result['routes'])
            
            result['computation_time_seconds'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Generación completada: {result['routes_generated']} rutas, "
                f"{result['total_orders_assigned']} pedidos asignados en "
                f"{result['computation_time_seconds']:.2f}s"
            )
            
            return result
        
        except Exception as e:
            logger.exception(f"Error generando rutas desde sales-service: {e}")
            result['status'] = 'failed'
            result['message'] = f'Error inesperado: {str(e)}'
            result['errors'].append(str(e))
            result['computation_time_seconds'] = (datetime.now() - start_time).total_seconds()
            return result
    
    def _validate_orders(self, orders: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """
        Valida que los pedidos tengan todos los datos necesarios.
        
        Validaciones:
        - Dirección de entrega completa
        - Coordenadas (lat/lng) o dirección geocodificable
        - Prioridad clínica
        - Peso y volumen estimado
        - Ventanas de entrega (opcional pero recomendado)
        
        Args:
            orders: Lista de pedidos desde sales-service
        
        Returns:
            Tupla (pedidos_válidos, pedidos_inválidos)
        """
        valid_orders = []
        invalid_orders = []
        
        for order in orders:
            validation_errors = []
            
            # Validar campos obligatorios
            if not order.get('id'):
                validation_errors.append('Falta ID de pedido')
            
            if not order.get('order_number'):
                validation_errors.append('Falta número de pedido')
            
            if not order.get('customer_id'):
                validation_errors.append('Falta ID de cliente')
            
            # Validar dirección
            delivery_address = order.get('delivery_address', '').strip()
            if not delivery_address or len(delivery_address) < 10:
                validation_errors.append('Dirección de entrega inválida o incompleta')
            
            # Validar coordenadas o capacidad de geocoding
            latitude = order.get('latitude')
            longitude = order.get('longitude')
            
            if latitude is None or longitude is None:
                # Si no hay coordenadas, debe tener ciudad y departamento para geocoding
                if not order.get('city') or not order.get('department'):
                    validation_errors.append('Faltan coordenadas o datos para geocodificar')
            else:
                # Validar rango de coordenadas (Colombia: lat 4-12, lng -78 a -66)
                if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                    validation_errors.append('Coordenadas fuera de rango válido')
            
            # Validar peso y volumen
            estimated_weight = order.get('estimated_weight_kg', 0)
            estimated_volume = order.get('estimated_volume_m3', 0)
            
            if estimated_weight <= 0:
                validation_errors.append('Peso estimado debe ser mayor a 0')
            
            if estimated_volume <= 0:
                validation_errors.append('Volumen estimado debe ser mayor a 0')
            
            # Validar prioridad clínica
            clinical_priority = order.get('clinical_priority', 3)
            if clinical_priority not in [1, 2, 3]:
                validation_errors.append('Prioridad clínica debe ser 1, 2 o 3')
            
            # Clasificar pedido
            if validation_errors:
                order['validation_error'] = '; '.join(validation_errors)
                invalid_orders.append(order)
            else:
                # Normalizar datos
                normalized_order = {
                    'order_id': order['id'],
                    'order_number': order['order_number'],
                    'customer_id': order['customer_id'],
                    'customer_name': order.get('customer_name', 'Desconocido'),
                    'delivery_address': delivery_address,
                    'city': order.get('city', ''),
                    'department': order.get('department', ''),
                    'latitude': latitude,
                    'longitude': longitude,
                    'clinical_priority': clinical_priority,
                    'requires_cold_chain': order.get('requires_cold_chain', False),
                    'estimated_weight_kg': float(estimated_weight),
                    'estimated_volume_m3': float(estimated_volume),
                    'delivery_time_window_start': order.get('delivery_time_window_start'),
                    'delivery_time_window_end': order.get('delivery_time_window_end'),
                    'special_instructions': order.get('special_instructions', ''),
                    'total_amount': order.get('total_amount', 0),
                    'items_count': order.get('items_count', 0)
                }
                valid_orders.append(normalized_order)
        
        return valid_orders, invalid_orders
    
    def _update_orders_in_sales_service(self, routes: List[Dict]):
        """
        Actualiza el estado de los pedidos asignados en sales-service.
        
        Acciones:
        - Marca pedidos como 'processing' (en ruta)
        - Registra is_routed = true
        - Asocia route_id
        
        Args:
            routes: Lista de rutas generadas (serializadas)
        """
        updated_count = 0
        failed_count = 0
        
        for route in routes:
            route_id = route.get('id')
            stops = route.get('stops', [])
            
            for stop in stops:
                assignments = stop.get('assignments', [])
                
                for assignment in assignments:
                    order_id = assignment.get('order_id')
                    
                    if not order_id:
                        continue
                    
                    try:
                        # Actualizar estado a 'processing'
                        success = self.sales_client.update_order_status(
                            order_id=order_id,
                            new_status='processing',
                            notes=f'Asignado a ruta {route.get("route_code")}'
                        )
                        
                        if success:
                            # Marcar como ruteado
                            self.sales_client._make_request(
                                'PUT',
                                f'/orders/{order_id}',
                                json_data={
                                    'is_routed': True,
                                    'route_id': route_id,
                                    'routed_at': datetime.utcnow().isoformat()
                                }
                            )
                            updated_count += 1
                        else:
                            failed_count += 1
                            logger.warning(f"No se pudo actualizar pedido {order_id}")
                    
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error actualizando pedido {order_id}: {e}")
        
        logger.info(
            f"Pedidos actualizados en sales-service: {updated_count} exitosos, "
            f"{failed_count} fallidos"
        )
