"""
Comando para reasignar pedidos entre rutas.
"""

from typing import Dict
from datetime import datetime
import logging

from src.models.delivery_route import DeliveryRoute
from src.models.route_stop import RouteStop
from src.models.route_assignment import RouteAssignment
from src.models.vehicle import Vehicle
from src.utils.route_validators import RouteValidator
from src.session import Session

logger = logging.getLogger(__name__)


class ReassignOrder:
    """
    Comando para reasignar un pedido de una ruta a otra.
    """
    
    def __init__(
        self,
        order_id: int,
        current_route_id: int,
        new_vehicle_id: int,
        reason: str,
        reassigned_by: str
    ):
        """
        Args:
            order_id: ID del pedido a reasignar
            current_route_id: ID de la ruta actual
            new_vehicle_id: ID del vehículo destino
            reason: Motivo de la reasignación
            reassigned_by: Usuario que realiza la reasignación
        """
        self.order_id = order_id
        self.current_route_id = current_route_id
        self.new_vehicle_id = new_vehicle_id
        self.reason = reason
        self.reassigned_by = reassigned_by
    
    def execute(self) -> Dict:
        """
        Ejecuta la reasignación del pedido.
        
        Flujo:
        1. Validar que el pedido existe en la ruta actual
        2. Validar que el nuevo vehículo existe y está disponible
        3. Validar restricciones (cadena de frío, capacidad)
        4. Buscar o crear ruta para el nuevo vehículo
        5. Mover el pedido a la nueva ruta
        6. Actualizar métricas de ambas rutas
        7. Registrar el cambio
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # 1. Obtener assignment actual
            assignment = Session.query(RouteAssignment).filter(
                RouteAssignment.order_id == self.order_id,
                RouteAssignment.route_id == self.current_route_id
            ).first()
            
            if not assignment:
                return {
                    'status': 'not_found',
                    'message': f'Pedido {self.order_id} no encontrado en ruta {self.current_route_id}'
                }
            
            current_route = Session.query(DeliveryRoute).get(self.current_route_id)
            if not current_route:
                return {
                    'status': 'error',
                    'message': f'Ruta actual {self.current_route_id} no encontrada'
                }
            
            # 2. Validar nuevo vehículo
            new_vehicle = Session.query(Vehicle).get(self.new_vehicle_id)
            if not new_vehicle:
                return {
                    'status': 'error',
                    'message': f'Vehículo {self.new_vehicle_id} no encontrado'
                }
            
            # 3. Validar restricciones
            vehicles_data = [{
                'id': new_vehicle.id,
                'has_refrigeration': new_vehicle.has_refrigeration,
                'is_available': new_vehicle.is_available
            }]
            
            validation = RouteValidator.validate_route_reassignment(
                order_id=self.order_id,
                current_route_id=self.current_route_id,
                new_vehicle_id=self.new_vehicle_id,
                vehicles=vehicles_data,
                reason=self.reason
            )
            
            if not validation['is_valid']:
                return {
                    'status': 'validation_error',
                    'message': 'La reasignación no pasó las validaciones',
                    'errors': validation['errors'],
                    'warnings': validation['warnings']
                }
            
            # 4. Verificar restricciones específicas del pedido
            if assignment.requires_cold_chain and not new_vehicle.has_refrigeration:
                return {
                    'status': 'error',
                    'message': (
                        f'El pedido {self.order_id} requiere cadena de frío pero el vehículo '
                        f'{new_vehicle.plate} no tiene refrigeración'
                    )
                }
            
            # 5. Buscar ruta existente para el nuevo vehículo en la misma fecha
            target_route = Session.query(DeliveryRoute).filter(
                DeliveryRoute.vehicle_id == self.new_vehicle_id,
                DeliveryRoute.planned_date == current_route.planned_date,
                DeliveryRoute.distribution_center_id == current_route.distribution_center_id,
                DeliveryRoute.status.in_(['draft', 'active'])
            ).first()
            
            # Si no existe, crear nueva ruta
            if not target_route:
                from src.services.route_optimizer_service import RouteOptimizerService
                
                route_code = RouteOptimizerService._generate_route_code(
                    current_route.distribution_center_id,
                    current_route.planned_date
                )
                
                target_route = DeliveryRoute(
                    route_code=route_code,
                    vehicle_id=new_vehicle.id,
                    driver_name=new_vehicle.driver_name,
                    generation_date=datetime.now(),
                    planned_date=current_route.planned_date,
                    status='draft',
                    distribution_center_id=current_route.distribution_center_id,
                    total_distance_km=0,
                    estimated_duration_minutes=0,
                    total_orders=0,
                    total_stops=0,
                    optimization_score=0,
                    has_cold_chain_products=assignment.requires_cold_chain,
                    created_by=self.reassigned_by
                )
                Session.add(target_route)
                Session.flush()
                
                logger.info(f"Creada nueva ruta {route_code} para vehículo {new_vehicle.plate}")
            
            # 6. Obtener stop actual
            current_stop = Session.query(RouteStop).get(assignment.stop_id)
            
            # 7. Crear nuevo stop en la ruta destino
            # Asignar como última parada (antes del retorno a depot)
            max_sequence = Session.query(RouteStop).filter(
                RouteStop.route_id == target_route.id
            ).count()
            
            new_stop = RouteStop(
                route_id=target_route.id,
                sequence_order=max_sequence,  # Se agregará al final
                stop_type='delivery',
                customer_id=current_stop.customer_id,
                customer_name=current_stop.customer_name,
                delivery_address=current_stop.delivery_address,
                latitude=current_stop.latitude,
                longitude=current_stop.longitude,
                city=current_stop.city,
                time_window_start=current_stop.time_window_start,
                time_window_end=current_stop.time_window_end,
                clinical_priority=current_stop.clinical_priority,
                requires_cold_chain=assignment.requires_cold_chain,
                status='pending'
            )
            Session.add(new_stop)
            Session.flush()
            
            # 8. Actualizar assignment
            assignment.was_reassigned = True
            assignment.reassigned_from_route_id = current_route.id
            assignment.reassignment_date = datetime.now()
            assignment.reassignment_reason = self.reason
            assignment.route_id = target_route.id
            assignment.stop_id = new_stop.id
            
            # 9. Eliminar stop anterior si no tiene más pedidos
            remaining_assignments = Session.query(RouteAssignment).filter(
                RouteAssignment.stop_id == current_stop.id,
                RouteAssignment.id != assignment.id
            ).count()
            
            if remaining_assignments == 0:
                Session.delete(current_stop)
            
            # 10. Actualizar métricas de ambas rutas
            self._update_route_metrics(current_route)
            self._update_route_metrics(target_route)
            
            # 11. Agregar nota a las rutas
            current_route.notes = (
                f"{current_route.notes or ''}\n\n"
                f"Pedido {self.order_id} reasignado a vehículo {new_vehicle.plate} "
                f"por {self.reassigned_by}: {self.reason}"
            )
            
            target_route.notes = (
                f"{target_route.notes or ''}\n\n"
                f"Pedido {self.order_id} reasignado desde ruta {current_route.route_code} "
                f"por {self.reassigned_by}: {self.reason}"
            )
            
            Session.commit()
            
            logger.info(
                f"Pedido {self.order_id} reasignado de ruta {current_route.route_code} "
                f"a {target_route.route_code} por {self.reassigned_by}"
            )
            
            return {
                'status': 'success',
                'message': (
                    f'Pedido {self.order_id} reasignado exitosamente de '
                    f'{current_route.route_code} a {target_route.route_code}'
                ),
                'from_route': current_route.to_dict(),
                'to_route': target_route.to_dict(),
                'warnings': validation.get('warnings', [])
            }
        
        except Exception as e:
            Session.rollback()
            logger.exception(f"Error reasignando pedido {self.order_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error al reasignar pedido: {str(e)}'
            }
    
    def _update_route_metrics(self, route: DeliveryRoute):
        """Actualiza las métricas de una ruta después de cambios."""
        from decimal import Decimal
        
        # Contar pedidos
        route.total_orders = Session.query(RouteAssignment).filter(
            RouteAssignment.route_id == route.id
        ).count()
        
        # Contar paradas (excluyendo depot)
        route.total_stops = Session.query(RouteStop).filter(
            RouteStop.route_id == route.id,
            RouteStop.stop_type == 'delivery'
        ).count()
        
        # Verificar cadena de frío
        has_cold_chain = Session.query(RouteAssignment).filter(
            RouteAssignment.route_id == route.id,
            RouteAssignment.requires_cold_chain == True
        ).count() > 0
        
        route.has_cold_chain_products = has_cold_chain
        route.updated_at = datetime.now()
        
        logger.debug(
            f"Métricas actualizadas para ruta {route.route_code}: "
            f"{route.total_orders} pedidos, {route.total_stops} paradas"
        )
