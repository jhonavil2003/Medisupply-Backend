"""
VRP (Vehicle Routing Problem) Solver usando OR-Tools de Google.

Este módulo resuelve el problema de ruteo de vehículos con las siguientes restricciones:
- Capacidad de vehículos (peso y volumen)
- Ventanas de tiempo para entregas
- Cadena de frío (solo vehículos refrigerados)
- Prioridad clínica (penalizar entregas tardías a clientes críticos)
- Máximo de paradas por ruta
"""

from typing import List, Dict
from datetime import datetime, time
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import logging

logger = logging.getLogger(__name__)


class VRPSolver:
    """
    Solucionador del Vehicle Routing Problem (VRP) con restricciones múltiples.
    """
    
    def __init__(
        self,
        vehicles: List[Dict],
        orders: List[Dict],
        distance_matrix_km: List[List[float]],
        time_matrix_minutes: List[List[float]],
        depot_index: int = 0,
        max_execution_time_seconds: int = 30
    ):
        """
        Inicializa el solver VRP.
        
        Args:
            vehicles: Lista de diccionarios con datos de vehículos
                {
                    'id': int,
                    'capacity_kg': float,
                    'capacity_m3': float,
                    'has_refrigeration': bool,
                    'temperature_min': float (opcional),
                    'temperature_max': float (opcional),
                    'max_stops': int,
                    'cost_per_km': float,
                    'avg_speed_kmh': float
                }
            orders: Lista de diccionarios con datos de pedidos
                {
                    'id': int,
                    'customer_name': str,
                    'address': str,
                    'latitude': float,
                    'longitude': float,
                    'weight_kg': float,
                    'volume_m3': float,
                    'requires_cold_chain': bool,
                    'temperature_min': float (opcional),
                    'temperature_max': float (opcional),
                    'clinical_priority': int (1=Crítico, 2=Alto, 3=Normal),
                    'time_window_start': time (opcional),
                    'time_window_end': time (opcional),
                    'service_time_minutes': int
                }
            distance_matrix_km: Matriz de distancias [depot, order1, order2, ...]
            time_matrix_minutes: Matriz de tiempos [depot, order1, order2, ...]
            depot_index: Índice del centro de distribución (usualmente 0)
            max_execution_time_seconds: Tiempo máximo de ejecución
        """
        self.vehicles = vehicles
        self.orders = orders
        self.distance_matrix_km = distance_matrix_km
        self.time_matrix_minutes = time_matrix_minutes
        self.depot_index = depot_index
        self.max_execution_time_seconds = max_execution_time_seconds
        
        self.num_vehicles = len(vehicles)
        self.num_locations = len(distance_matrix_km)  # depot + orders
        
        # Validaciones
        self._validate_inputs()
    
    def _validate_inputs(self):
        """Valida que los inputs sean consistentes."""
        if self.num_locations != len(self.orders) + 1:
            raise ValueError(
                f"La matriz de distancias tiene {self.num_locations} ubicaciones "
                f"pero hay {len(self.orders)} pedidos (debería ser {len(self.orders) + 1} con depot)"
            )
        
        if len(self.distance_matrix_km) != len(self.time_matrix_minutes):
            raise ValueError("Matrices de distancia y tiempo tienen dimensiones diferentes")
        
        if self.num_vehicles == 0:
            raise ValueError("No hay vehículos disponibles")
        
        if len(self.orders) == 0:
            raise ValueError("No hay pedidos para rutear")
    
    def solve(self, optimization_objective: str = 'balanced') -> Dict:
        """
        Resuelve el VRP y retorna las rutas optimizadas.
        
        Args:
            optimization_objective: Estrategia de optimización
                - 'minimize_distance': Minimizar distancia total
                - 'minimize_time': Minimizar tiempo total
                - 'minimize_cost': Minimizar costo operativo
                - 'balanced': Balance entre costo, tiempo y prioridades
        
        Returns:
            Dict con la solución:
            {
                'status': 'success' | 'partial' | 'failed',
                'routes': [
                    {
                        'vehicle_id': int,
                        'vehicle_index': int,
                        'stops': [
                            {
                                'location_index': int,
                                'order_id': int (None si es depot),
                                'sequence_order': int,
                                'arrival_time_minutes': float,
                                'cumulative_load_kg': float,
                                'cumulative_load_m3': float
                            }
                        ],
                        'total_distance_km': float,
                        'total_time_minutes': float,
                        'total_load_kg': float,
                        'total_load_m3': float,
                        'orders_count': int
                    }
                ],
                'unassigned_orders': List[int],
                'total_distance_km': float,
                'total_time_minutes': float,
                'total_cost': float,
                'optimization_score': float,
                'computation_time_seconds': float
            }
        """
        start_time = datetime.now()
        
        try:
            # Crear manager y modelo de routing
            manager = pywrapcp.RoutingIndexManager(
                self.num_locations,
                self.num_vehicles,
                self.depot_index
            )
            routing = pywrapcp.RoutingModel(manager)
            
            # 1. Registrar función de costo (distancia o tiempo según objetivo)
            if optimization_objective == 'minimize_time':
                transit_callback_index = self._register_time_callback(manager, routing)
            else:
                transit_callback_index = self._register_distance_callback(manager, routing)
            
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            
            # 2. Agregar dimensión de capacidad (peso)
            self._add_capacity_dimension_weight(manager, routing)
            
            # 3. Agregar dimensión de capacidad (volumen)
            self._add_capacity_dimension_volume(manager, routing)
            
            # 4. Agregar dimensión de tiempo (ventanas de entrega)
            self._add_time_dimension(manager, routing)
            
            # 5. Agregar restricción de cadena de frío
            self._add_cold_chain_constraints(manager, routing)
            
            # 6. Agregar restricción de máximo de paradas
            self._add_max_stops_constraint(routing)
            
            # 7. Agregar penalización por prioridad clínica
            self._add_priority_penalties(manager, routing)
            
            # 8. Permitir pedidos no asignados si es necesario (con penalización alta)
            self._allow_unassigned_orders(manager, routing)
            
            # 9. Configurar parámetros de búsqueda
            search_parameters = self._configure_search_parameters(optimization_objective)
            
            # 10. Resolver
            logger.info(f"Iniciando solver VRP con {len(self.orders)} pedidos y {self.num_vehicles} vehículos")
            solution = routing.SolveWithParameters(search_parameters)
            
            computation_time = (datetime.now() - start_time).total_seconds()
            
            # 11. Extraer solución
            if solution:
                result = self._extract_solution(manager, routing, solution)
                result['computation_time_seconds'] = computation_time
                
                logger.info(
                    f"Solver completado en {computation_time:.2f}s. "
                    f"Rutas: {len(result['routes'])}, "
                    f"Pedidos asignados: {len(self.orders) - len(result['unassigned_orders'])}"
                )
                
                return result
            else:
                logger.error("No se encontró solución para el VRP")
                return {
                    'status': 'failed',
                    'routes': [],
                    'unassigned_orders': [order['id'] for order in self.orders],
                    'error': 'No se encontró solución factible',
                    'computation_time_seconds': computation_time
                }
        
        except Exception as e:
            logger.exception(f"Error en solver VRP: {e}")
            return {
                'status': 'failed',
                'routes': [],
                'unassigned_orders': [order['id'] for order in self.orders],
                'error': str(e),
                'computation_time_seconds': (datetime.now() - start_time).total_seconds()
            }
    
    def _register_distance_callback(self, manager, routing):
        """Registra callback de distancia."""
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(self.distance_matrix_km[from_node][to_node] * 1000)  # Convertir a metros
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        return transit_callback_index
    
    def _register_time_callback(self, manager, routing):
        """Registra callback de tiempo."""
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(self.time_matrix_minutes[from_node][to_node])
        
        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        return transit_callback_index
    
    def _add_capacity_dimension_weight(self, manager, routing):
        """Agrega restricción de capacidad de peso."""
        def weight_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == self.depot_index:
                return 0
            order_index = from_node - 1
            return int(self.orders[order_index]['weight_kg'] * 100)  # Convertir a gramos/10
        
        weight_callback_index = routing.RegisterUnaryTransitCallback(weight_callback)
        
        # Capacidades de cada vehículo
        vehicle_capacities = [int(v['capacity_kg'] * 100) for v in self.vehicles]
        
        routing.AddDimensionWithVehicleCapacity(
            weight_callback_index,
            0,  # slack_max
            vehicle_capacities,
            True,  # start_cumul_to_zero
            'Capacity_Weight'
        )
    
    def _add_capacity_dimension_volume(self, manager, routing):
        """Agrega restricción de capacidad de volumen."""
        def volume_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            if from_node == self.depot_index:
                return 0
            order_index = from_node - 1
            return int(self.orders[order_index]['volume_m3'] * 1000)  # Convertir a litros
        
        volume_callback_index = routing.RegisterUnaryTransitCallback(volume_callback)
        
        # Capacidades de cada vehículo
        vehicle_capacities = [int(v['capacity_m3'] * 1000) for v in self.vehicles]
        
        routing.AddDimensionWithVehicleCapacity(
            volume_callback_index,
            0,  # slack_max
            vehicle_capacities,
            True,  # start_cumul_to_zero
            'Capacity_Volume'
        )
    
    def _add_time_dimension(self, manager, routing):
        """Agrega dimensión de tiempo con ventanas de entrega."""
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_time = int(self.time_matrix_minutes[from_node][to_node])
            
            # Agregar tiempo de servicio del nodo de origen
            if from_node != self.depot_index:
                order_index = from_node - 1
                service_time = self.orders[order_index].get('service_time_minutes', 15)
                travel_time += service_time
            
            return travel_time
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        
        # Horizonte de tiempo: un día completo (1440 minutos)
        horizon = 1440
        
        routing.AddDimension(
            time_callback_index,
            horizon,  # slack_max (espera permitida)
            horizon,  # capacity (máximo tiempo de ruta)
            False,    # start_cumul_to_zero
            'Time'
        )
        
        time_dimension = routing.GetDimensionOrDie('Time')
        
        # Establecer ventanas de tiempo para cada pedido
        for order_idx, order in enumerate(self.orders):
            location_idx = order_idx + 1  # +1 porque depot es 0
            index = manager.NodeToIndex(location_idx)
            
            if order.get('time_window_start') and order.get('time_window_end'):
                # Convertir time a minutos desde medianoche
                start_minutes = self._time_to_minutes(order['time_window_start'])
                end_minutes = self._time_to_minutes(order['time_window_end'])
                
                time_dimension.CumulVar(index).SetRange(start_minutes, end_minutes)
            else:
                # Sin ventana específica, permitir todo el día (8:00 - 18:00)
                time_dimension.CumulVar(index).SetRange(480, 1080)
        
        # Minimizar tiempo total de todas las rutas
        time_dimension.SetGlobalSpanCostCoefficient(100)
    
    def _add_cold_chain_constraints(self, manager, routing):
        """
        Agrega restricción de cadena de frío:
        Pedidos con cold_chain solo pueden ir en vehículos refrigerados.
        """
        for order_idx, order in enumerate(self.orders):
            if order.get('requires_cold_chain', False):
                location_idx = order_idx + 1
                index = manager.NodeToIndex(location_idx)
                
                # Permitir solo en vehículos refrigerados
                allowed_vehicles = []
                for vehicle_idx, vehicle in enumerate(self.vehicles):
                    if vehicle.get('has_refrigeration', False):
                        # Verificar compatibilidad de temperatura si está especificada
                        if self._is_temperature_compatible(order, vehicle):
                            allowed_vehicles.append(vehicle_idx)
                
                if not allowed_vehicles:
                    logger.warning(
                        f"Pedido {order['id']} requiere cadena de frío pero no hay "
                        f"vehículos refrigerados disponibles"
                    )
                    # Penalizar mucho este pedido para que quede sin asignar
                    routing.AddDisjunction([index], 1000000)
                else:
                    # Permitir solo en vehículos refrigerados
                    routing.VehicleVar(index).SetValues(allowed_vehicles)
    
    def _is_temperature_compatible(self, order: Dict, vehicle: Dict) -> bool:
        """Verifica si las temperaturas del pedido son compatibles con el vehículo."""
        order_temp_min = order.get('temperature_min')
        order_temp_max = order.get('temperature_max')
        vehicle_temp_min = vehicle.get('temperature_min')
        vehicle_temp_max = vehicle.get('temperature_max')
        
        if order_temp_min is None or order_temp_max is None:
            return True  # Sin restricción específica
        
        if vehicle_temp_min is None or vehicle_temp_max is None:
            return True  # Vehículo sin restricción
        
        # Verificar que los rangos se superpongan
        return not (order_temp_max < vehicle_temp_min or order_temp_min > vehicle_temp_max)
    
    def _add_max_stops_constraint(self, routing):
        """Agrega restricción de máximo de paradas por vehículo."""
        for vehicle_idx, vehicle in enumerate(self.vehicles):
            max_stops = vehicle.get('max_stops', 20)
            
            # Contar el número de paradas (excluyendo depot)
            routing.AddConstantDimension(
                1,  # Incremento de 1 por cada visita
                max_stops,
                True,  # start_cumul_to_zero
                f'Stop_Count_{vehicle_idx}'
            )
    
    def _add_priority_penalties(self, manager, routing):
        """
        Agrega penalizaciones por prioridad clínica.
        Entregas tardías a clientes críticos tienen mayor penalización.
        """
        time_dimension = routing.GetDimensionOrDie('Time')
        
        for order_idx, order in enumerate(self.orders):
            location_idx = order_idx + 1
            index = manager.NodeToIndex(location_idx)
            
            clinical_priority = order.get('clinical_priority', 3)
            
            # Penalización inversamente proporcional a la prioridad
            # Prioridad 1 (crítico) = alta penalización por tardanza
            # Prioridad 3 (normal) = baja penalización
            penalty = (4 - clinical_priority) * 10000
            
            time_dimension.SetCumulVarSoftUpperBound(index, 1080, penalty)  # 1080 = 18:00
    
    def _allow_unassigned_orders(self, manager, routing):
        """
        Permite que algunos pedidos queden sin asignar si no hay capacidad.
        Se aplica una penalización muy alta para minimizar esto.
        """
        penalty = 10000000  # Penalización muy alta
        
        for order_idx in range(len(self.orders)):
            location_idx = order_idx + 1
            index = manager.NodeToIndex(location_idx)
            routing.AddDisjunction([index], penalty)
    
    def _configure_search_parameters(self, optimization_objective: str):
        """Configura parámetros de búsqueda del solver."""
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        
        # Estrategia de primera solución
        if optimization_objective == 'balanced':
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            )
        elif optimization_objective == 'minimize_time':
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
            )
        else:
            search_parameters.first_solution_strategy = (
                routing_enums_pb2.FirstSolutionStrategy.SAVINGS
            )
        
        # Metaheurística local
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        
        # Límite de tiempo
        search_parameters.time_limit.seconds = self.max_execution_time_seconds
        
        # Logging
        search_parameters.log_search = False
        
        return search_parameters
    
    def _extract_solution(self, manager, routing, solution) -> Dict:
        """Extrae las rutas de la solución."""
        routes = []
        unassigned_orders = []
        total_distance_km = 0
        total_time_minutes = 0
        total_cost = 0
        
        time_dimension = routing.GetDimensionOrDie('Time')
        weight_dimension = routing.GetDimensionOrDie('Capacity_Weight')
        volume_dimension = routing.GetDimensionOrDie('Capacity_Volume')
        
        # Identificar pedidos no asignados
        for order_idx in range(len(self.orders)):
            location_idx = order_idx + 1
            index = manager.NodeToIndex(location_idx)
            if solution.Value(routing.NextVar(index)) == index:
                unassigned_orders.append(self.orders[order_idx]['id'])
        
        # Extraer rutas de cada vehículo
        for vehicle_idx in range(self.num_vehicles):
            index = routing.Start(vehicle_idx)
            route_stops = []
            route_distance = 0
            route_time = 0
            sequence = 0
            
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                time_var = time_dimension.CumulVar(index)
                weight_var = weight_dimension.CumulVar(index)
                volume_var = volume_dimension.CumulVar(index)
                
                stop = {
                    'location_index': node,
                    'order_id': None if node == self.depot_index else self.orders[node - 1]['id'],
                    'sequence_order': sequence,
                    'arrival_time_minutes': solution.Min(time_var),
                    'cumulative_load_kg': solution.Value(weight_var) / 100.0,
                    'cumulative_load_m3': solution.Value(volume_var) / 1000.0
                }
                route_stops.append(stop)
                
                # Siguiente parada
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_idx)
                sequence += 1
            
            # Agregar última parada (regreso a depot)
            node = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)
            route_stops.append({
                'location_index': node,
                'order_id': None,
                'sequence_order': sequence,
                'arrival_time_minutes': solution.Min(time_var),
                'cumulative_load_kg': 0,
                'cumulative_load_m3': 0
            })
            
            # Solo agregar rutas con paradas (más allá del depot)
            if len(route_stops) > 2:
                route_time = solution.Min(time_var)
                route_distance_km = route_distance / 1000.0
                vehicle = self.vehicles[vehicle_idx]
                route_cost = route_distance_km * vehicle.get('cost_per_km', 5.0)
                
                routes.append({
                    'vehicle_id': vehicle['id'],
                    'vehicle_index': vehicle_idx,
                    'stops': route_stops,
                    'total_distance_km': route_distance_km,
                    'total_time_minutes': route_time,
                    'total_load_kg': max(s['cumulative_load_kg'] for s in route_stops),
                    'total_load_m3': max(s['cumulative_load_m3'] for s in route_stops),
                    'orders_count': len([s for s in route_stops if s['order_id'] is not None])
                })
                
                total_distance_km += route_distance_km
                total_time_minutes += route_time
                total_cost += route_cost
        
        # Calcular score de optimización (0-100)
        optimization_score = self._calculate_optimization_score(
            routes, unassigned_orders, total_distance_km
        )
        
        status = 'success'
        if len(unassigned_orders) > 0:
            status = 'partial'
            logger.warning(f"{len(unassigned_orders)} pedidos quedaron sin asignar")
        
        return {
            'status': status,
            'routes': routes,
            'unassigned_orders': unassigned_orders,
            'total_distance_km': round(total_distance_km, 2),
            'total_time_minutes': int(total_time_minutes),
            'total_cost': round(total_cost, 2),
            'optimization_score': optimization_score
        }
    
    def _calculate_optimization_score(
        self, routes: List[Dict], unassigned_orders: List[int], total_distance_km: float
    ) -> float:
        """
        Calcula un score de optimización de 0 a 100.
        
        Considera:
        - % de pedidos asignados
        - Utilización de capacidad de vehículos
        - Balance de carga entre rutas
        """
        if not routes:
            return 0.0
        
        # 1. Score por asignación (50%)
        assigned_orders = len(self.orders) - len(unassigned_orders)
        assignment_score = (assigned_orders / len(self.orders)) * 50
        
        # 2. Score por utilización de capacidad (30%)
        capacity_utilizations = []
        for route in routes:
            vehicle = next(v for v in self.vehicles if v['id'] == route['vehicle_id'])
            weight_utilization = route['total_load_kg'] / vehicle['capacity_kg']
            volume_utilization = route['total_load_m3'] / vehicle['capacity_m3']
            capacity_utilizations.append(max(weight_utilization, volume_utilization))
        
        avg_utilization = sum(capacity_utilizations) / len(capacity_utilizations)
        capacity_score = avg_utilization * 30
        
        # 3. Score por balance de carga (20%)
        if len(routes) > 1:
            distances = [r['total_distance_km'] for r in routes]
            avg_distance = sum(distances) / len(distances)
            variance = sum((d - avg_distance) ** 2 for d in distances) / len(distances)
            balance_score = max(0, 20 - (variance / avg_distance) * 10)
        else:
            balance_score = 20
        
        total_score = assignment_score + capacity_score + balance_score
        return round(min(100, total_score), 2)
    
    @staticmethod
    def _time_to_minutes(t: time) -> int:
        """Convierte time a minutos desde medianoche."""
        return t.hour * 60 + t.minute
    
    @staticmethod
    def solve_tsp(
        distance_matrix: List[List[float]],
        start_index: int = 0,
        return_to_start: bool = False
    ) -> Dict:
        """
        Resuelve el Travelling Salesman Problem (TSP) - variante simple de VRP para un solo vehículo.
        
        Args:
            distance_matrix: Matriz de distancias entre ubicaciones
            start_index: Índice de la ubicación inicial
            return_to_start: Si debe regresar al punto de inicio
        
        Returns:
            {
                'sequence': List[int],  # Secuencia óptima de índices
                'total_distance': float,  # Distancia total en km
                'total_time': float  # Tiempo total estimado en minutos
            }
        """
        num_locations = len(distance_matrix)
        
        if num_locations == 0:
            return {
                'sequence': [],
                'total_distance': 0.0,
                'total_time': 0.0
            }
        
        if num_locations == 1:
            return {
                'sequence': [0],
                'total_distance': 0.0,
                'total_time': 0.0
            }
        
        # Crear manager para TSP
        manager = pywrapcp.RoutingIndexManager(
            num_locations,
            1,  # Un solo vehículo
            start_index
        )
        
        # Crear modelo de routing
        routing = pywrapcp.RoutingModel(manager)
        
        # Definir función de costo (distancia)
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node] * 100)  # Multiplicar por 100 para precision
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Configurar parámetros de búsqueda
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 10
        
        # Resolver
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            logger.warning("No se encontró solución TSP, usando orden original")
            return {
                'sequence': list(range(num_locations)),
                'total_distance': sum(distance_matrix[i][i+1] for i in range(num_locations-1)),
                'total_time': sum(distance_matrix[i][i+1] for i in range(num_locations-1)) * 2  # ~30 km/h
            }
        
        # Extraer secuencia
        sequence = []
        total_distance = 0.0
        index = routing.Start(0)
        
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            sequence.append(node)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            if not routing.IsEnd(index):
                from_node = manager.IndexToNode(previous_index)
                to_node = manager.IndexToNode(index)
                total_distance += distance_matrix[from_node][to_node]
        
        # Agregar última ubicación si retorna al inicio
        if return_to_start and len(sequence) > 0:
            last_node = manager.IndexToNode(index)
            total_distance += distance_matrix[sequence[-1]][last_node]
        
        # Estimar tiempo total (asumiendo 30 km/h promedio)
        total_time = total_distance * 2  # minutos
        
        return {
            'sequence': sequence,
            'total_distance': round(total_distance, 2),
            'total_time': round(total_time, 1)
        }
