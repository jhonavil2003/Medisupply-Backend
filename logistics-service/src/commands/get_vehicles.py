"""
Comandos para gestión de vehículos de la flota.
"""

from typing import List, Optional, Dict
from datetime import datetime, date
from decimal import Decimal
import logging

from src.models.vehicle import Vehicle
from src.session import Session

logger = logging.getLogger(__name__)


class GetVehicles:
    """
    Comando para consultar vehículos con filtros.
    """
    
    def __init__(
        self,
        distribution_center_id: Optional[int] = None,
        is_available: Optional[bool] = None,
        has_refrigeration: Optional[bool] = None,
        vehicle_type: Optional[str] = None
    ):
        """
        Args:
            distribution_center_id: Filtrar por centro de distribución
            is_available: Filtrar por disponibilidad
            has_refrigeration: Filtrar por capacidad de refrigeración
            vehicle_type: Filtrar por tipo (van, truck, refrigerated_truck)
        """
        self.distribution_center_id = distribution_center_id
        self.is_available = is_available
        self.has_refrigeration = has_refrigeration
        self.vehicle_type = vehicle_type
    
    def execute(self) -> Dict:
        """
        Ejecuta la consulta de vehículos.
        
        Returns:
            Dict con lista de vehículos y estadísticas
        """
        try:
            query = Session.query(Vehicle)
            
            # Aplicar filtros
            if self.distribution_center_id:
                query = query.filter(
                    Vehicle.home_distribution_center_id == self.distribution_center_id
                )
            
            if self.is_available is not None:
                query = query.filter(Vehicle.is_available == self.is_available)
            
            if self.has_refrigeration is not None:
                query = query.filter(Vehicle.has_refrigeration == self.has_refrigeration)
            
            if self.vehicle_type:
                query = query.filter(Vehicle.vehicle_type == self.vehicle_type)
            
            vehicles = query.all()
            
            # Estadísticas
            total_vehicles = len(vehicles)
            available_count = sum(1 for v in vehicles if v.is_available)
            refrigerated_count = sum(1 for v in vehicles if v.has_refrigeration)
            
            total_capacity_kg = sum(float(v.capacity_kg) for v in vehicles if v.is_available)
            total_capacity_m3 = sum(float(v.capacity_m3) for v in vehicles if v.is_available)
            
            vehicles_data = [v.to_dict(include_distribution_center=True) for v in vehicles]
            
            return {
                'status': 'success',
                'vehicles': vehicles_data,
                'statistics': {
                    'total_vehicles': total_vehicles,
                    'available': available_count,
                    'unavailable': total_vehicles - available_count,
                    'with_refrigeration': refrigerated_count,
                    'total_capacity_kg': round(total_capacity_kg, 2),
                    'total_capacity_m3': round(total_capacity_m3, 2)
                }
            }
        
        except Exception as e:
            logger.exception(f"Error consultando vehículos: {e}")
            return {
                'status': 'error',
                'message': f'Error al consultar vehículos: {str(e)}',
                'vehicles': []
            }


class GetVehicleById:
    """
    Comando para obtener detalle de un vehículo.
    """
    
    def __init__(self, vehicle_id: int):
        self.vehicle_id = vehicle_id
    
    def execute(self) -> Dict:
        """
        Obtiene detalle completo del vehículo.
        """
        try:
            vehicle = Session.query(Vehicle).get(self.vehicle_id)
            
            if not vehicle:
                return {
                    'status': 'not_found',
                    'message': f'Vehículo {self.vehicle_id} no encontrado'
                }
            
            vehicle_data = vehicle.to_dict(include_distribution_center=True)
            
            return {
                'status': 'success',
                'vehicle': vehicle_data
            }
        
        except Exception as e:
            logger.exception(f"Error obteniendo vehículo {self.vehicle_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error al obtener vehículo: {str(e)}'
            }


class UpdateVehicleAvailability:
    """
    Comando para actualizar disponibilidad de un vehículo.
    """
    
    def __init__(self, vehicle_id: int, is_available: bool, reason: Optional[str] = None):
        """
        Args:
            vehicle_id: ID del vehículo
            is_available: Nueva disponibilidad
            reason: Motivo del cambio (opcional)
        """
        self.vehicle_id = vehicle_id
        self.is_available = is_available
        self.reason = reason
    
    def execute(self) -> Dict:
        """
        Actualiza la disponibilidad del vehículo.
        """
        try:
            vehicle = Session.query(Vehicle).get(self.vehicle_id)
            
            if not vehicle:
                return {
                    'status': 'not_found',
                    'message': f'Vehículo {self.vehicle_id} no encontrado'
                }
            
            old_status = vehicle.is_available
            vehicle.is_available = self.is_available
            vehicle.updated_at = datetime.now()
            
            Session.commit()
            
            status_change = "disponible" if self.is_available else "no disponible"
            logger.info(
                f"Vehículo {vehicle.plate} marcado como {status_change}"
                f"{f': {self.reason}' if self.reason else ''}"
            )
            
            return {
                'status': 'success',
                'message': f'Vehículo {vehicle.plate} ahora está {status_change}',
                'vehicle': vehicle.to_dict()
            }
        
        except Exception as e:
            Session.rollback()
            logger.exception(f"Error actualizando disponibilidad de vehículo {self.vehicle_id}: {e}")
            return {
                'status': 'error',
                'message': f'Error al actualizar disponibilidad: {str(e)}'
            }


class GetAvailableVehicles:
    """
    Comando para obtener vehículos disponibles para una fecha y centro específicos.
    """
    
    def __init__(self, distribution_center_id: int, planned_date: date = None):
        """
        Args:
            distribution_center_id: ID del centro de distribución
            planned_date: Fecha planeada (para verificar asignaciones futuras)
        """
        self.distribution_center_id = distribution_center_id
        self.planned_date = planned_date or datetime.now().date()
    
    def execute(self) -> Dict:
        """
        Obtiene vehículos disponibles.
        
        Un vehículo está disponible si:
        - is_available = True
        - No tiene rutas activas o en progreso para la fecha
        """
        try:
            from src.models.delivery_route import DeliveryRoute
            
            # Obtener vehículos básicamente disponibles
            vehicles = Session.query(Vehicle).filter(
                Vehicle.home_distribution_center_id == self.distribution_center_id,
                Vehicle.is_available == True
            ).all()
            
            # Filtrar vehículos con rutas activas en la fecha
            available_vehicles = []
            for vehicle in vehicles:
                active_routes = Session.query(DeliveryRoute).filter(
                    DeliveryRoute.vehicle_id == vehicle.id,
                    DeliveryRoute.planned_date == self.planned_date,
                    DeliveryRoute.status.in_(['active', 'in_progress'])
                ).count()
                
                if active_routes == 0:
                    available_vehicles.append(vehicle)
            
            vehicles_data = [v.to_dict() for v in available_vehicles]
            
            # Calcular capacidad total disponible
            total_capacity_kg = sum(float(v.capacity_kg) for v in available_vehicles)
            total_capacity_m3 = sum(float(v.capacity_m3) for v in available_vehicles)
            refrigerated_count = sum(1 for v in available_vehicles if v.has_refrigeration)
            
            return {
                'status': 'success',
                'date': self.planned_date.isoformat(),
                'distribution_center_id': self.distribution_center_id,
                'vehicles': vehicles_data,
                'summary': {
                    'total_available': len(available_vehicles),
                    'with_refrigeration': refrigerated_count,
                    'total_capacity_kg': round(total_capacity_kg, 2),
                    'total_capacity_m3': round(total_capacity_m3, 2)
                }
            }
        
        except Exception as e:
            logger.exception(f"Error obteniendo vehículos disponibles: {e}")
            return {
                'status': 'error',
                'message': f'Error al obtener vehículos disponibles: {str(e)}',
                'vehicles': []
            }
