"""
Servicio de alto nivel para optimización de rutas de entrega.

Este servicio orquesta:
1. Geocodificación de direcciones (con caché)
2. Cálculo de matrices de distancia/tiempo
3. Clasificación de pedidos por restricciones
4. Ejecución del algoritmo VRP
5. Creación de objetos DeliveryRoute, RouteStop, RouteAssignment
"""

from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import logging

from src.models.vehicle import Vehicle
from src.models.delivery_route import DeliveryRoute
from src.models.route_stop import RouteStop
from src.models.route_assignment import RouteAssignment
from src.models.distribution_center import DistributionCenter
from src.services.google_maps_service import get_google_maps_service
from src.utils.vrp_solver import VRPSolver
from src.session import Session

logger = logging.getLogger(__name__)


class RouteOptimizerService:
    """
    Servicio de optimización de rutas de entrega.
    """
    
    @staticmethod
    def optimize_routes(
        orders: List[Dict],
        distribution_center_id: int,
        planned_date: date,
        optimization_strategy: str = 'balanced',  # DEFAULT: Balancea distancia, tiempo, capacidad y equidad
        max_execution_time: int = 30
    ) -> Dict:
        """
        Genera rutas optimizadas para los pedidos dados.
        
        Args:
            orders: Lista de pedidos con estructura:
                {
                    'id': int,                        # ID del pedido (sales-service)
                    'order_number': str,              # Número de pedido
                    'customer_id': int,
                    'customer_name': str,
                    'delivery_address': str,
                    'city': str,
                    'department': str,
                    'latitude': float (opcional),     # Si ya está geocodificado
                    'longitude': float (opcional),
                    'weight_kg': float,
                    'volume_m3': float,
                    'requires_cold_chain': bool,
                    'temperature_min': float (opcional),
                    'temperature_max': float (opcional),
                    'clinical_priority': int,         # 1=Crítico, 2=Alto, 3=Normal
                    'time_window_start': time (opcional),
                    'time_window_end': time (opcional),
                    'service_time_minutes': int (opcional, default=15)
                }
            distribution_center_id: ID del centro de distribución
            planned_date: Fecha planeada de entrega
            optimization_strategy: Estrategia de optimización
                - 'balanced': Balance entre costo, tiempo y prioridades
                - 'minimize_time': Prioriza tiempo de entrega
                - 'minimize_distance': Minimiza distancia recorrida
                - 'minimize_cost': Minimiza costo operativo
                - 'priority_first': Entrega primero a clientes críticos
            max_execution_time: Tiempo máximo de ejecución en segundos
        
        Returns:
            Dict con resultado:
            {
                'status': 'success' | 'partial' | 'failed',
                'routes': List[DeliveryRoute],
                'unassigned_orders': List[Dict],
                'metrics': {
                    'total_routes': int,
                    'total_orders_assigned': int,
                    'total_distance_km': float,
                    'total_time_minutes': int,
                    'total_cost': float,
                    'optimization_score': float
                },
                'computation_time_seconds': float,
                'errors': List[str]
            }
        """
        start_time = datetime.now()
        errors = []
        
        try:
            # 1. Validar y obtener centro de distribución
            distribution_center = Session.get(DistributionCenter, distribution_center_id)
            if not distribution_center:
                raise ValueError(f"Centro de distribución {distribution_center_id} no encontrado")
            
            # 2. Obtener vehículos disponibles
            vehicles = RouteOptimizerService._get_available_vehicles(distribution_center_id)
            if not vehicles:
                return {
                    'status': 'failed',
                    'routes': [],
                    'unassigned_orders': orders,
                    'metrics': {},
                    'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'errors': ['No hay vehículos disponibles']
                }
            
            logger.info(f"Optimizando rutas con {len(orders)} pedidos y {len(vehicles)} vehículos")
            
            # 3. Geocodificar direcciones (con caché)
            geocoded_orders, geocoding_errors = RouteOptimizerService._geocode_orders(orders)
            if geocoding_errors:
                errors.extend(geocoding_errors)
            
            if not geocoded_orders:
                return {
                    'status': 'failed',
                    'routes': [],
                    'unassigned_orders': orders,
                    'metrics': {},
                    'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'errors': errors + ['No se pudo geocodificar ninguna dirección']
                }
            
            # 4. Preparar coordenadas (depot + orders)
            depot_coords = (
                float(distribution_center.latitude),
                float(distribution_center.longitude)
            )
            order_coords = [
                (float(order['latitude']), float(order['longitude']))
                for order in geocoded_orders
            ]
            all_coords = [depot_coords] + order_coords
            
            # 5. Obtener matriz de distancias y tiempos
            logger.info("Calculando matriz de distancias...")
            distance_matrix, time_matrix, matrix_errors = RouteOptimizerService._get_distance_matrix(
                all_coords
            )
            if matrix_errors:
                errors.extend(matrix_errors)
            
            # 6. Preparar datos para VRP solver
            vehicle_data = [
                {
                    'id': v.id,
                    'capacity_kg': float(v.capacity_kg),
                    'capacity_m3': float(v.capacity_m3),
                    'has_refrigeration': v.has_refrigeration,
                    'temperature_min': float(v.temperature_min) if v.temperature_min else None,
                    'temperature_max': float(v.temperature_max) if v.temperature_max else None,
                    'max_stops': v.max_stops_per_route or 20,
                    'cost_per_km': float(v.cost_per_km),
                    'avg_speed_kmh': float(v.avg_speed_kmh) if v.avg_speed_kmh else 40.0
                }
                for v in vehicles
            ]
            
            order_data = [
                {
                    'id': order['id'],
                    'customer_name': order['customer_name'],
                    'address': order['delivery_address'],
                    'latitude': order['latitude'],
                    'longitude': order['longitude'],
                    'weight_kg': order['weight_kg'],
                    'volume_m3': order['volume_m3'],
                    'requires_cold_chain': order.get('requires_cold_chain', False),
                    'temperature_min': order.get('temperature_min'),
                    'temperature_max': order.get('temperature_max'),
                    'clinical_priority': order.get('clinical_priority', 3),
                    'time_window_start': order.get('time_window_start'),
                    'time_window_end': order.get('time_window_end'),
                    'service_time_minutes': order.get('service_time_minutes', 15)
                }
                for order in geocoded_orders
            ]
            
            # 7. Ejecutar solver VRP
            logger.info("Ejecutando solver VRP...")
            solver = VRPSolver(
                vehicles=vehicle_data,
                orders=order_data,
                distance_matrix_km=distance_matrix,
                time_matrix_minutes=time_matrix,
                depot_index=0,
                max_execution_time_seconds=max_execution_time
            )
            
            solution = solver.solve(optimization_objective=optimization_strategy)
            
            if solution['status'] == 'failed':
                return {
                    'status': 'failed',
                    'routes': [],
                    'unassigned_orders': orders,
                    'metrics': {},
                    'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                    'errors': errors + [solution.get('error', 'Solver falló')]
                }
            
            # 8. Crear objetos DeliveryRoute, RouteStop, RouteAssignment
            logger.info("Creando objetos de ruta en base de datos...")
            routes_objects, creation_errors = RouteOptimizerService._create_route_objects(
                solution=solution,
                vehicles=vehicles,
                orders=geocoded_orders,
                distribution_center=distribution_center,
                planned_date=planned_date,
                polyline=None  # TODO: Generar polyline con Google Directions API
            )
            
            if creation_errors:
                errors.extend(creation_errors)
            
            # 9. Identificar pedidos no asignados
            unassigned_order_ids = solution.get('unassigned_orders', [])
            unassigned_orders = [
                order for order in orders
                if order['id'] in unassigned_order_ids
            ]
            
            # 10. Calcular métricas totales
            metrics = {
                'total_routes': len(routes_objects),
                'total_orders_assigned': len(orders) - len(unassigned_orders),
                'total_distance_km': solution['total_distance_km'],
                'total_time_minutes': solution['total_time_minutes'],
                'total_cost': solution['total_cost'],
                'optimization_score': solution['optimization_score']
            }
            
            computation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Optimización completada en {computation_time:.2f}s. "
                f"Rutas: {metrics['total_routes']}, "
                f"Pedidos asignados: {metrics['total_orders_assigned']}/{len(orders)}"
            )
            
            return {
                'status': solution['status'],
                'routes': routes_objects,
                'unassigned_orders': unassigned_orders,
                'metrics': metrics,
                'computation_time_seconds': computation_time,
                'errors': errors if errors else []
            }
        
        except Exception as e:
            logger.exception(f"Error en optimización de rutas: {e}")
            return {
                'status': 'failed',
                'routes': [],
                'unassigned_orders': orders,
                'metrics': {},
                'computation_time_seconds': (datetime.now() - start_time).total_seconds(),
                'errors': errors + [str(e)]
            }
    
    @staticmethod
    def _get_available_vehicles(distribution_center_id: int) -> List[Vehicle]:
        """Obtiene vehículos disponibles para el centro de distribución."""
        vehicles = Session.query(Vehicle).filter_by(
            home_distribution_center_id=distribution_center_id,
            is_available=True
        ).all()
        
        logger.info(f"Encontrados {len(vehicles)} vehículos disponibles")
        return vehicles
    
    @staticmethod
    def _geocode_orders(orders: List[Dict]) -> tuple:
        """
        Geocodifica direcciones de pedidos (usando caché cuando sea posible).
        
        Returns:
            (geocoded_orders, errors)
        """
        google_maps = get_google_maps_service()
        geocoded_orders = []
        errors = []
        
        for order in orders:
            # Si ya tiene coordenadas, usar esas
            if order.get('latitude') and order.get('longitude'):
                geocoded_orders.append(order)
                continue
            
            # Geocodificar usando Google Maps
            try:
                result = google_maps.geocode_address(
                    address=order['delivery_address'],
                    city=order['city'],
                    department=order.get('department', ''),
                    country='Colombia',
                    use_cache=True
                )
                
                # La función geocode_address devuelve directamente el resultado o lanza excepción
                order['latitude'] = result['lat']
                order['longitude'] = result['lng']
                order['formatted_address'] = result.get('formatted_address', order['delivery_address'])
                geocoded_orders.append(order)
                logger.info(f"[OK] Geocodificado: {order['order_number']} -> ({result['lat']}, {result['lng']})")
            
            except Exception as e:
                error_msg = f"Error geocodificando pedido {order['order_number']}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        logger.info(f"Geocodificados {len(geocoded_orders)}/{len(orders)} pedidos")
        return geocoded_orders, errors
    
    @staticmethod
    def _get_distance_matrix(coordinates: List[tuple]) -> tuple:
        """
        Obtiene matriz de distancias y tiempos entre todas las ubicaciones.
        
        Returns:
            (distance_matrix_km, time_matrix_minutes, errors)
        """
        google_maps = get_google_maps_service()
        errors = []
        
        try:
            result = google_maps.get_distance_matrix(
                origins=coordinates,
                destinations=coordinates,
                mode='driving'
            )
            
            # La función get_distance_matrix devuelve directamente el resultado o lanza excepción
            logger.info(f"✅ Matriz de distancias obtenida de Google Maps: {result['origins_count']}×{result['destinations_count']}")
            return result['distances_km'], result['durations_minutes'], []
        
        except Exception as e:
            error_msg = f"Error calculando matriz de distancias: {e}"
            logger.warning(error_msg)
            logger.info("⚠️  Usando distancias euclidianas como fallback")
            errors.append(error_msg)
            
            # Fallback a distancia euclidiana
            distance_matrix = RouteOptimizerService._calculate_euclidean_matrix(coordinates)
            time_matrix = [[d / 0.5 for d in row] for row in distance_matrix]  # Asumir 30 km/h
            
            return distance_matrix, time_matrix, errors
    
    @staticmethod
    def _calculate_euclidean_matrix(coordinates: List[tuple]) -> List[List[float]]:
        """Calcula matriz de distancias euclidianas (fallback)."""
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1, lon1, lat2, lon2):
            """Calcula distancia haversine en km."""
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Radio de la Tierra en km
            return c * r
        
        n = len(coordinates)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    lat1, lon1 = coordinates[i]
                    lat2, lon2 = coordinates[j]
                    matrix[i][j] = haversine(lat1, lon1, lat2, lon2)
        
        return matrix
    
    @staticmethod
    def _create_route_objects(
        solution: Dict,
        vehicles: List[Vehicle],
        orders: List[Dict],
        distribution_center: DistributionCenter,
        planned_date: date,
        polyline: Optional[str]
    ) -> tuple:
        """
        Crea objetos DeliveryRoute, RouteStop, RouteAssignment en la BD.
        
        Returns:
            (routes, errors)
        """
        routes_objects = []
        errors = []
        
        try:
            for route_data in solution['routes']:
                # Buscar vehículo
                vehicle = next(
                    (v for v in vehicles if v.id == route_data['vehicle_id']),
                    None
                )
                if not vehicle:
                    errors.append(f"Vehículo {route_data['vehicle_id']} no encontrado")
                    continue
                
                # Crear DeliveryRoute
                route_code = RouteOptimizerService._generate_route_code(
                    distribution_center.id,
                    planned_date
                )
                
                delivery_route = DeliveryRoute(
                    route_code=route_code,
                    vehicle_id=vehicle.id,
                    driver_name=vehicle.driver_name,
                    generation_date=datetime.now(),
                    planned_date=planned_date,
                    status='draft',
                    total_distance_km=Decimal(str(route_data['total_distance_km'])),
                    estimated_duration_minutes=route_data['total_time_minutes'],
                    total_orders=route_data['orders_count'],
                    total_stops=len(route_data['stops']) - 2,  # Excluir depot inicio y fin
                    optimization_score=Decimal(str(solution['optimization_score'])),
                    has_cold_chain_products=any(
                        order.get('requires_cold_chain', False)
                        for order in orders
                        if order['id'] in [s['order_id'] for s in route_data['stops'] if s['order_id']]
                    ),
                    distribution_center_id=distribution_center.id,
                    estimated_start_time=RouteOptimizerService._minutes_to_datetime(
                        planned_date, route_data['stops'][0]['arrival_time_minutes']
                    ),
                    polyline=polyline
                )
                
                Session.add(delivery_route)
                Session.flush()  # Para obtener el ID
                
                # Crear RouteStops y RouteAssignments
                for stop_data in route_data['stops']:
                    location_index = stop_data['location_index']
                    
                    # Determinar tipo de parada
                    if location_index == 0:
                        stop_type = 'depot' if stop_data['sequence_order'] == 0 else 'return'
                        customer_id = None
                        customer_name = distribution_center.name
                        delivery_address = distribution_center.address
                        latitude = distribution_center.latitude
                        longitude = distribution_center.longitude
                        city = distribution_center.city
                    else:
                        stop_type = 'delivery'
                        order = orders[location_index - 1]
                        customer_id = order['customer_id']
                        customer_name = order['customer_name']
                        delivery_address = order['delivery_address']
                        latitude = Decimal(str(order['latitude']))
                        longitude = Decimal(str(order['longitude']))
                        city = order['city']
                    
                    # Crear RouteStop
                    route_stop = RouteStop(
                        route_id=delivery_route.id,
                        sequence_order=stop_data['sequence_order'],
                        stop_type=stop_type,
                        customer_id=customer_id,
                        customer_name=customer_name,
                        delivery_address=delivery_address,
                        latitude=latitude,
                        longitude=longitude,
                        city=city,
                        estimated_arrival_time=RouteOptimizerService._minutes_to_datetime(
                            planned_date, stop_data['arrival_time_minutes']
                        )
                    )
                    
                    Session.add(route_stop)
                    Session.flush()
                    
                    # Crear RouteAssignment si es una entrega
                    if stop_type == 'delivery':
                        order = orders[location_index - 1]
                        route_assignment = RouteAssignment(
                            route_id=delivery_route.id,
                            stop_id=route_stop.id,
                            order_id=order['id'],
                            order_number=order['order_number'],
                            requires_cold_chain=order.get('requires_cold_chain', False),
                            total_weight_kg=Decimal(str(order['weight_kg'])),
                            total_volume_m3=Decimal(str(order['volume_m3'])),
                            clinical_priority=order.get('clinical_priority', 3),
                            assignment_date=datetime.now()
                        )
                        Session.add(route_assignment)
                
                routes_objects.append(delivery_route)
            
            # Commit todas las rutas
            Session.commit()
            logger.info(f"Creadas {len(routes_objects)} rutas en la base de datos")
        
        except Exception as e:
            Session.rollback()
            error_msg = f"Error creando objetos de ruta: {e}"
            logger.exception(error_msg)
            errors.append(error_msg)
        
        return routes_objects, errors
    
    @staticmethod
    def _generate_route_code(distribution_center_id: int, planned_date: date) -> str:
        """Genera código único para la ruta."""
        from src.models.delivery_route import DeliveryRoute
        
        # Contar rutas del día
        count = Session.query(DeliveryRoute).filter(
            DeliveryRoute.distribution_center_id == distribution_center_id,
            DeliveryRoute.planned_date == planned_date
        ).count()
        
        return f"ROUTE-{planned_date.strftime('%Y%m%d')}-DC{distribution_center_id}-{count + 1:03d}"
    
    @staticmethod
    def _minutes_to_datetime(base_date: date, minutes: float) -> datetime:
        """Convierte minutos desde medianoche a datetime."""
        return datetime.combine(base_date, time(0, 0)) + timedelta(minutes=int(minutes))
