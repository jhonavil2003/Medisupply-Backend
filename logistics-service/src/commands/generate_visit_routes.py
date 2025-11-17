"""
Comando para generar rutas optimizadas de visitas a clientes.

Similar a GenerateRoutesCommand pero adaptado para visitas comerciales
en lugar de entregas de pedidos.
"""

import logging
from typing import List, Dict, Optional
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from src.models.visit_route import VisitRoute, VisitRouteStatus
from src.models.visit_route_stop import VisitRouteStop
from src.services.sales_service_client import get_sales_service_client
from src.services.google_maps_service import get_google_maps_service
from src.utils.vrp_solver import VRPSolver
from src.session import Session

logger = logging.getLogger(__name__)


class GenerateVisitRoutesCommand:
    """
    Genera ruta optimizada para que un vendedor visite múltiples clientes.
    
    Flujo:
    1. Obtener datos de clientes desde sales-service
    2. Geocodificar direcciones (si es necesario)
    3. Calcular matriz de distancias entre clientes
    4. Ejecutar algoritmo VRP para optimizar secuencia
    5. Crear objetos VisitRoute y VisitRouteStop
    6. Retornar ruta optimizada
    """
    
    def __init__(
        self,
        salesperson_id: int,
        salesperson_name: str,
        salesperson_employee_id: str,
        customer_ids: List[int],
        planned_date: date,
        optimization_strategy: str = 'minimize_distance',
        start_location: Optional[Dict] = None,
        end_location: Optional[Dict] = None,
        work_start_time: time = time(8, 0),
        work_end_time: time = time(18, 0),
        service_time_per_visit_minutes: int = 30
    ):
        """
        Args:
            salesperson_id: ID del vendedor
            salesperson_name: Nombre del vendedor
            salesperson_employee_id: Código de empleado del vendedor
            customer_ids: Lista de IDs de clientes a visitar
            planned_date: Fecha planeada para las visitas
            optimization_strategy: Estrategia de optimización
                - 'minimize_distance': Minimiza distancia total (DEFAULT)
                - 'minimize_time': Minimiza tiempo total
                - 'balanced': Balance entre distancia y tiempo
            start_location: Punto de inicio (opcional)
                {
                    'name': 'Oficina Central',
                    'latitude': 4.6097,
                    'longitude': -74.0817,
                    'address': 'Calle 100 #20-30'
                }
            end_location: Punto de fin (opcional, si es diferente del inicio)
            work_start_time: Hora de inicio de jornada
            work_end_time: Hora de fin de jornada
            service_time_per_visit_minutes: Tiempo estimado por visita
        """
        self.salesperson_id = salesperson_id
        self.salesperson_name = salesperson_name
        self.salesperson_employee_id = salesperson_employee_id
        self.customer_ids = customer_ids
        self.planned_date = planned_date
        self.optimization_strategy = optimization_strategy
        self.start_location = start_location
        self.end_location = end_location or start_location  # Si no hay fin, usar inicio
        self.work_start_time = work_start_time
        self.work_end_time = work_end_time
        self.service_time_per_visit_minutes = service_time_per_visit_minutes
        
        self.sales_client = get_sales_service_client()
        self.maps_service = get_google_maps_service()
        
    def execute(self) -> Dict:
        """
        Ejecuta la generación de ruta de visitas.
        
        Returns:
            {
                'status': 'success' | 'partial' | 'failed',
                'route': VisitRoute,
                'metrics': {
                    'total_stops': int,
                    'total_distance_km': float,
                    'estimated_duration_minutes': int,
                    'optimization_score': float
                },
                'warnings': List[str],
                'errors': List[str],
                'computation_time_seconds': float
            }
        """
        start_time = datetime.now()
        errors = []
        warnings = []
        
        try:
            logger.info(f"🚀 Iniciando generación de ruta de visitas")
            logger.info(f"   Vendedor: {self.salesperson_name} (ID: {self.salesperson_id})")
            logger.info(f"   Clientes: {len(self.customer_ids)}")
            logger.info(f"   Fecha: {self.planned_date}")
            logger.info(f"   Estrategia: {self.optimization_strategy}")
            
            # PASO 1: Obtener datos de clientes
            logger.info("📥 PASO 1: Obteniendo datos de clientes...")
            customers_result = self._fetch_customers_data()
            
            if customers_result['not_found']:
                warning_msg = f"Clientes no encontrados: {customers_result['not_found']}"
                warnings.append(warning_msg)
                logger.warning(f"⚠️  {warning_msg}")
            
            if not customers_result['customers']:
                error_msg = "No se encontraron clientes válidos para visitar"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                return self._build_error_response(errors, warnings, start_time)
            
            customers = customers_result['customers']
            logger.info(f"✅ {len(customers)} clientes obtenidos")
            
            # PASO 2: Validar y preparar ubicaciones
            logger.info("📍 PASO 2: Validando ubicaciones...")
            locations, location_errors = self._prepare_locations(customers)
            
            if location_errors:
                errors.extend(location_errors)
                logger.error(f"❌ Errores en ubicaciones: {len(location_errors)}")
            
            if not locations:
                error_msg = "No hay ubicaciones válidas para optimizar"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
                return self._build_error_response(errors, warnings, start_time)
            
            logger.info(f"✅ {len(locations)} ubicaciones válidas")
            
            # PASO 3: Calcular matriz de distancias
            logger.info("🗺️  PASO 3: Calculando distancias...")
            distance_matrix, distance_errors = self._calculate_distances(locations)
            
            if distance_errors:
                warnings.extend(distance_errors)
            
            logger.info(f"✅ Matriz de distancias calculada")
            
            # PASO 4: Optimizar secuencia de visitas
            logger.info("🧮 PASO 4: Optimizando secuencia de visitas...")
            optimized_sequence = self._optimize_sequence(locations, distance_matrix)
            
            logger.info(f"✅ Secuencia optimizada: {optimized_sequence['sequence']}")
            logger.info(f"   Distancia total: {optimized_sequence['total_distance_km']:.2f} km")
            logger.info(f"   Tiempo estimado: {optimized_sequence['total_time_minutes']} min")
            
            # PASO 5: Crear objetos de ruta
            logger.info("💾 PASO 5: Creando ruta en base de datos...")
            visit_route = self._create_route_objects(
                customers,
                optimized_sequence,
                distance_matrix
            )
            
            logger.info(f"✅ Ruta creada: {visit_route.route_code}")
            
            # Calcular tiempo total
            computation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"🎉 Generación completada en {computation_time:.2f} segundos")
            
            return {
                'status': 'success' if not errors else 'partial',
                'route': visit_route,
                'metrics': {
                    'total_stops': len(visit_route.stops),
                    'total_distance_km': float(visit_route.total_distance_km or 0),
                    'estimated_duration_minutes': visit_route.estimated_duration_minutes,
                    'optimization_score': float(visit_route.optimization_score or 0)
                },
                'warnings': warnings,
                'errors': errors,
                'computation_time_seconds': computation_time
            }
            
        except Exception as e:
            logger.error(f"❌ Error crítico generando ruta: {e}", exc_info=True)
            errors.append(f"Error crítico: {str(e)}")
            return self._build_error_response(errors, warnings, start_time)
    
    def _fetch_customers_data(self) -> Dict:
        """
        Obtiene datos de clientes desde sales-service.
        
        Returns:
            {
                'customers': List[Dict],
                'not_found': List[int]
            }
        """
        try:
            result = self.sales_client.get_customers_by_ids(self.customer_ids)
            return {
                'customers': result.get('customers', []),
                'not_found': result.get('not_found', [])
            }
        except Exception as e:
            logger.error(f"Error obteniendo clientes: {e}")
            raise
    
    def _prepare_locations(self, customers: List[Dict]) -> tuple:
        """
        Prepara y valida ubicaciones de clientes.
        
        Args:
            customers: Lista de clientes con sus datos
        
        Returns:
            (locations, errors)
            - locations: Lista de ubicaciones válidas
            - errors: Lista de mensajes de error
        """
        locations = []
        errors = []
        
        for customer in customers:
            # Validar coordenadas
            if not customer.get('latitude') or not customer.get('longitude'):
                error_msg = f"Cliente {customer['id']} ({customer.get('business_name')}) sin coordenadas GPS"
                errors.append(error_msg)
                logger.warning(f"⚠️  {error_msg}")
                continue
            
            location = {
                'customer_id': customer['id'],
                'customer_name': customer['business_name'],
                'customer_document': customer.get('document_number'),
                'customer_type': customer.get('customer_type'),
                'latitude': float(customer['latitude']),
                'longitude': float(customer['longitude']),
                'address': customer.get('address'),
                'neighborhood': customer.get('neighborhood'),
                'city': customer.get('city'),
                'department': customer.get('department'),
                'contact_name': customer.get('contact_name'),
                'contact_phone': customer.get('contact_phone'),
                'contact_email': customer.get('contact_email'),
                'service_time_minutes': self.service_time_per_visit_minutes
            }
            
            locations.append(location)
        
        return locations, errors
    
    def _calculate_distances(self, locations: List[Dict]) -> tuple:
        """
        Calcula matriz de distancias entre ubicaciones.
        
        Args:
            locations: Lista de ubicaciones
        
        Returns:
            (distance_matrix, errors)
        """
        errors = []
        
        try:
            # Preparar coordenadas para Google Maps
            coordinates = [
                (loc['latitude'], loc['longitude'])
                for loc in locations
            ]
            
            # Agregar punto de inicio si existe
            if self.start_location:
                coordinates.insert(0, (
                    self.start_location['latitude'],
                    self.start_location['longitude']
                ))
            
            # Calcular matriz usando Google Maps (con caché)
            distance_matrix = self.maps_service.calculate_distance_matrix(
                origins=coordinates,
                destinations=coordinates
            )
            
            return distance_matrix, errors
            
        except Exception as e:
            error_msg = f"Error calculando distancias: {str(e)}"
            errors.append(error_msg)
            logger.warning(f"⚠️  {error_msg}")
            
            # Fallback: Usar distancias euclidianas
            logger.info("📐 Usando distancias euclidianas como fallback")
            distance_matrix = self._calculate_euclidean_distances(locations)
            
            return distance_matrix, errors
    
    def _calculate_euclidean_distances(self, locations: List[Dict]) -> Dict:
        """
        Calcula distancias euclidianas como fallback.
        
        Args:
            locations: Lista de ubicaciones
        
        Returns:
            Matriz de distancias
        """
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lat1, lon1, lat2, lon2):
            """Calcula distancia entre dos puntos GPS en km"""
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            km = 6371 * c
            return km
        
        n = len(locations)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    distance_km = haversine(
                        locations[i]['latitude'],
                        locations[i]['longitude'],
                        locations[j]['latitude'],
                        locations[j]['longitude']
                    )
                    matrix[i][j] = distance_km
        
        return {
            'distances_km': matrix,
            'durations_minutes': [[d * 2 for d in row] for row in matrix]  # Estimar ~30 km/h
        }
    
    def _optimize_sequence(self, locations: List[Dict], distance_matrix: Dict) -> Dict:
        """
        Optimiza la secuencia de visitas usando algoritmo VRP.
        
        Args:
            locations: Lista de ubicaciones
            distance_matrix: Matriz de distancias
        
        Returns:
            {
                'sequence': List[int],  # Índices en orden óptimo
                'total_distance_km': float,
                'total_time_minutes': int
            }
        """
        # Configurar problema
        num_locations = len(locations)
        distances = distance_matrix.get('distances_km', [])
        
        # Resolver TSP (Travelling Salesman Problem)
        # Como es un solo vendedor, es TSP en lugar de VRP
        result = VRPSolver.solve_tsp(
            distance_matrix=distances,
            start_index=0,  # Comenzar desde oficina o primer cliente
            return_to_start=bool(self.end_location)  # Regresar si hay punto de fin
        )
        
        sequence = result.get('sequence', list(range(num_locations)))
        total_distance = result.get('total_distance', 0)
        total_time = result.get('total_time', 0)
        
        return {
            'sequence': sequence,
            'total_distance_km': total_distance,
            'total_time_minutes': total_time
        }
    
    def _create_route_objects(
        self,
        customers: List[Dict],
        optimized_sequence: Dict,
        distance_matrix: Dict
    ) -> VisitRoute:
        """
        Crea objetos VisitRoute y VisitRouteStop en la base de datos.
        
        Args:
            customers: Datos de clientes
            optimized_sequence: Secuencia optimizada
            distance_matrix: Matriz de distancias
        
        Returns:
            VisitRoute creado
        """
        # Crear objeto VisitRoute
        route_code = VisitRoute.generate_route_code(
            self.salesperson_id,
            self.planned_date
        )
        
        visit_route = VisitRoute(
            route_code=route_code,
            salesperson_id=self.salesperson_id,
            salesperson_name=self.salesperson_name,
            salesperson_employee_id=self.salesperson_employee_id,
            planned_date=self.planned_date,
            status=VisitRouteStatus.DRAFT,
            optimization_strategy=self.optimization_strategy,
            work_start_time=self.work_start_time,
            work_end_time=self.work_end_time
        )
        
        # Agregar ubicación de inicio/fin si existe
        if self.start_location:
            visit_route.start_location_name = self.start_location.get('name')
            visit_route.start_latitude = self.start_location['latitude']
            visit_route.start_longitude = self.start_location['longitude']
        
        if self.end_location:
            visit_route.end_location_name = self.end_location.get('name')
            visit_route.end_latitude = self.end_location['latitude']
            visit_route.end_longitude = self.end_location['longitude']
        
        Session.add(visit_route)
        Session.flush()  # Para obtener el ID
        
        # Crear paradas en el orden optimizado
        sequence = optimized_sequence['sequence']
        distances = distance_matrix.get('distances_km', [])
        durations = distance_matrix.get('durations_minutes', [])
        
        current_time = datetime.combine(self.planned_date, self.work_start_time)
        previous_index = 0
        
        for order, customer_index in enumerate(sequence, start=1):
            customer_data = customers[customer_index]
            
            # Calcular distancia y tiempo desde parada anterior
            if order == 1:
                distance_from_previous = 0.0
                travel_time = 0.0
            else:
                distance_from_previous = float(distances[previous_index][customer_index])
                travel_time = float(durations[previous_index][customer_index])
            
            # Calcular tiempos estimados
            current_time += timedelta(minutes=travel_time)
            arrival_time = current_time
            departure_time = arrival_time + timedelta(minutes=self.service_time_per_visit_minutes)
            
            # Crear parada
            stop = VisitRouteStop(
                route_id=visit_route.id,
                sequence_order=order,
                customer_id=customer_data['id'],
                customer_name=customer_data['business_name'],
                customer_document=customer_data.get('document_number'),
                customer_type=customer_data.get('customer_type'),
                address=customer_data.get('address'),
                neighborhood=customer_data.get('neighborhood'),
                city=customer_data.get('city'),
                department=customer_data.get('department'),
                latitude=customer_data['latitude'],
                longitude=customer_data['longitude'],
                contact_name=customer_data.get('contact_name'),
                contact_phone=customer_data.get('contact_phone'),
                contact_email=customer_data.get('contact_email'),
                estimated_arrival_time=arrival_time,
                estimated_departure_time=departure_time,
                estimated_service_time_minutes=self.service_time_per_visit_minutes,
                distance_from_previous_km=distance_from_previous,
                travel_time_from_previous_minutes=travel_time
            )
            
            Session.add(stop)
            
            # Actualizar para siguiente iteración
            current_time = departure_time
            previous_index = customer_index
        
        # Actualizar métricas de la ruta
        visit_route.update_metrics()
        visit_route.optimization_score = optimized_sequence.get('optimization_score', 85.0)
        
        # Generar URL de Google Maps
        visit_route.map_url = visit_route.generate_google_maps_url()
        
        # Guardar todo
        Session.commit()
        
        logger.info(f"✅ Ruta guardada: {visit_route.route_code} con {len(visit_route.stops)} paradas")
        
        return visit_route
    
    def _build_error_response(self, errors: List[str], warnings: List[str], start_time: datetime) -> Dict:
        """
        Construye respuesta de error.
        
        Args:
            errors: Lista de errores
            warnings: Lista de advertencias
            start_time: Tiempo de inicio
        
        Returns:
            Dict con información del error
        """
        computation_time = (datetime.now() - start_time).total_seconds()
        
        return {
            'status': 'failed',
            'route': None,
            'metrics': None,
            'warnings': warnings,
            'errors': errors,
            'computation_time_seconds': computation_time
        }
