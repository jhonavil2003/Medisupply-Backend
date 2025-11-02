"""
Validadores para rutas de entrega.

Verifica que las rutas generadas cumplan con todas las restricciones y sean factibles.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RouteValidator:
    """
    Valida soluciones de rutas de entrega.
    """
    
    @staticmethod
    def validate_solution(
        solution: Dict,
        vehicles: List[Dict],
        orders: List[Dict],
        max_distance_per_route_km: float = 300.0,
        max_time_per_route_minutes: int = 600
    ) -> Dict:
        """
        Valida una solución completa de rutas.
        
        Args:
            solution: Solución del VRP solver
            vehicles: Lista de vehículos disponibles
            orders: Lista de pedidos originales
            max_distance_per_route_km: Máxima distancia permitida por ruta
            max_time_per_route_minutes: Máximo tiempo permitido por ruta
        
        Returns:
            Dict con resultado de validación:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        if solution['status'] == 'failed':
            errors.append("La solución del solver falló")
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        routes = solution.get('routes', [])
        
        # 1. Verificar que hay al menos una ruta
        if not routes:
            errors.append("No se generaron rutas")
        
        # 2. Validar cada ruta individualmente
        for route_idx, route in enumerate(routes):
            route_errors, route_warnings = RouteValidator._validate_single_route(
                route=route,
                vehicles=vehicles,
                orders=orders,
                route_number=route_idx + 1,
                max_distance_km=max_distance_per_route_km,
                max_time_minutes=max_time_per_route_minutes
            )
            errors.extend(route_errors)
            warnings.extend(route_warnings)
        
        # 3. Verificar pedidos no asignados
        unassigned_count = len(solution.get('unassigned_orders', []))
        if unassigned_count > 0:
            warnings.append(
                f"{unassigned_count} pedido(s) quedaron sin asignar. "
                f"Esto puede deberse a falta de capacidad o restricciones no cumplidas."
            )
        
        # 4. Verificar duplicados (un pedido asignado a múltiples rutas)
        assigned_order_ids = []
        for route in routes:
            for stop in route['stops']:
                if stop['order_id']:
                    if stop['order_id'] in assigned_order_ids:
                        errors.append(f"Pedido {stop['order_id']} asignado a múltiples rutas")
                    assigned_order_ids.append(stop['order_id'])
        
        # 5. Verificar que todos los pedidos asignados existan
        order_ids = {order['id'] for order in orders}
        for order_id in assigned_order_ids:
            if order_id not in order_ids:
                errors.append(f"Ruta contiene pedido inexistente: {order_id}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info("Solución validada exitosamente")
        else:
            logger.error(f"Solución inválida con {len(errors)} errores")
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings
        }
    
    @staticmethod
    def _validate_single_route(
        route: Dict,
        vehicles: List[Dict],
        orders: List[Dict],
        route_number: int,
        max_distance_km: float,
        max_time_minutes: int
    ) -> tuple:
        """
        Valida una ruta individual.
        
        Returns:
            (errors, warnings)
        """
        errors = []
        warnings = []
        
        vehicle_id = route.get('vehicle_id')
        vehicle = next((v for v in vehicles if v['id'] == vehicle_id), None)
        
        if not vehicle:
            errors.append(f"Ruta {route_number}: Vehículo {vehicle_id} no encontrado")
            return errors, warnings
        
        # 1. Validar capacidad de peso
        max_load_kg = route.get('total_load_kg', 0)
        vehicle_capacity_kg = vehicle['capacity_kg']
        
        if max_load_kg > vehicle_capacity_kg:
            errors.append(
                f"Ruta {route_number}: Sobrecarga de peso. "
                f"Carga: {max_load_kg:.2f} kg, Capacidad: {vehicle_capacity_kg:.2f} kg"
            )
        elif max_load_kg > vehicle_capacity_kg * 0.95:
            warnings.append(
                f"Ruta {route_number}: Carga de peso al {max_load_kg/vehicle_capacity_kg*100:.1f}% de capacidad"
            )
        
        # 2. Validar capacidad de volumen
        max_load_m3 = route.get('total_load_m3', 0)
        vehicle_capacity_m3 = vehicle['capacity_m3']
        
        if max_load_m3 > vehicle_capacity_m3:
            errors.append(
                f"Ruta {route_number}: Sobrecarga de volumen. "
                f"Volumen: {max_load_m3:.2f} m³, Capacidad: {vehicle_capacity_m3:.2f} m³"
            )
        elif max_load_m3 > vehicle_capacity_m3 * 0.95:
            warnings.append(
                f"Ruta {route_number}: Carga de volumen al {max_load_m3/vehicle_capacity_m3*100:.1f}% de capacidad"
            )
        
        # 3. Validar distancia
        total_distance = route.get('total_distance_km', 0)
        if total_distance > max_distance_km:
            errors.append(
                f"Ruta {route_number}: Distancia excesiva. "
                f"Distancia: {total_distance:.2f} km, Máximo: {max_distance_km} km"
            )
        elif total_distance > max_distance_km * 0.9:
            warnings.append(
                f"Ruta {route_number}: Distancia al {total_distance/max_distance_km*100:.1f}% del máximo"
            )
        
        # 4. Validar tiempo
        total_time = route.get('total_time_minutes', 0)
        if total_time > max_time_minutes:
            errors.append(
                f"Ruta {route_number}: Tiempo excesivo. "
                f"Tiempo: {total_time} min, Máximo: {max_time_minutes} min"
            )
        elif total_time > max_time_minutes * 0.9:
            warnings.append(
                f"Ruta {route_number}: Tiempo al {total_time/max_time_minutes*100:.1f}% del máximo"
            )
        
        # 5. Validar cadena de frío
        stops = route.get('stops', [])
        order_ids_in_route = [s['order_id'] for s in stops if s['order_id']]
        
        has_cold_chain_orders = False
        for order_id in order_ids_in_route:
            order = next((o for o in orders if o['id'] == order_id), None)
            if order and order.get('requires_cold_chain', False):
                has_cold_chain_orders = True
                break
        
        if has_cold_chain_orders and not vehicle.get('has_refrigeration', False):
            errors.append(
                f"Ruta {route_number}: Pedidos con cadena de frío asignados a vehículo sin refrigeración"
            )
        
        # 6. Validar número de paradas
        delivery_stops = [s for s in stops if s.get('order_id') is not None]
        max_stops = vehicle.get('max_stops', 20)
        
        if len(delivery_stops) > max_stops:
            errors.append(
                f"Ruta {route_number}: Demasiadas paradas. "
                f"Paradas: {len(delivery_stops)}, Máximo: {max_stops}"
            )
        elif len(delivery_stops) > max_stops * 0.9:
            warnings.append(
                f"Ruta {route_number}: {len(delivery_stops)} paradas (cerca del máximo de {max_stops})"
            )
        
        # 7. Validar que la ruta comienza y termina en depot
        if len(stops) < 2:
            errors.append(f"Ruta {route_number}: Ruta inválida con menos de 2 paradas")
        else:
            first_stop = stops[0]
            last_stop = stops[-1]
            
            # Depot tiene location_index = 0
            if first_stop.get('location_index') != 0:
                errors.append(f"Ruta {route_number}: No comienza en depot")
            
            if last_stop.get('location_index') != 0:
                errors.append(f"Ruta {route_number}: No termina en depot")
        
        # 8. Validar secuencia de paradas
        for i, stop in enumerate(stops):
            if stop['sequence_order'] != i:
                errors.append(
                    f"Ruta {route_number}: Secuencia incorrecta en parada {i} "
                    f"(esperado: {i}, actual: {stop['sequence_order']})"
                )
        
        return errors, warnings
    
    @staticmethod
    def validate_route_reassignment(
        order_id: int,
        current_route_id: int,
        new_vehicle_id: int,
        vehicles: List[Dict],
        reason: str
    ) -> Dict:
        """
        Valida una reasignación manual de pedido.
        
        Returns:
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        # 1. Validar que el vehículo nuevo existe
        new_vehicle = next((v for v in vehicles if v['id'] == new_vehicle_id), None)
        if not new_vehicle:
            errors.append(f"Vehículo {new_vehicle_id} no encontrado")
            return {'is_valid': False, 'errors': errors, 'warnings': warnings}
        
        # 2. Validar que el vehículo está disponible
        if not new_vehicle.get('is_available', False):
            errors.append(f"Vehículo {new_vehicle_id} no está disponible")
        
        # 3. Validar que hay un motivo de reasignación
        if not reason or len(reason.strip()) < 5:
            errors.append("Debe proporcionar un motivo válido para la reasignación (mínimo 5 caracteres)")
        
        # 4. Advertencia si es una reasignación urgente
        urgent_keywords = ['avería', 'falla', 'accidente', 'emergencia', 'urgente']
        if any(keyword in reason.lower() for keyword in urgent_keywords):
            warnings.append("Reasignación marcada como urgente. Verificar disponibilidad inmediata del vehículo.")
        
        is_valid = len(errors) == 0
        
        return {
            'is_valid': is_valid,
            'errors': errors,
            'warnings': warnings
        }
