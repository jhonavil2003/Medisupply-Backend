"""
Tests para services/route_optimizer_service.py

Coverage objetivo: >70%

Funcionalidad a probar:
- optimize_routes (flujo principal)
- Geocodificación de direcciones
- Cálculo de matrices de distancia
- Obtención de vehículos disponibles
- Creación de objetos de ruta
- Manejo de errores
"""

import pytest
from datetime import date, time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from src.services.route_optimizer_service import RouteOptimizerService


class TestRouteOptimizerServiceBasic:
    """Tests básicos del RouteOptimizerService"""

    @patch('src.services.route_optimizer_service.Session')
    @patch('src.services.route_optimizer_service.get_google_maps_service')
    def test_optimize_routes_no_distribution_center(self, mock_gmaps, mock_session):
        """Test: Error cuando no existe el centro de distribución"""
        mock_session.get.return_value = None
        
        orders = [{'id': 101, 'customer_name': 'Cliente 1', 'delivery_address': 'Calle 1'}]
        
        result = RouteOptimizerService.optimize_routes(
            orders=orders,
            distribution_center_id=999,
            planned_date=date(2025, 11, 20)
        )
        
        assert result['status'] == 'failed'
        assert 'no encontrado' in str(result.get('errors', [''])[0]).lower()

    @patch('src.services.route_optimizer_service.Session')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._get_available_vehicles')
    def test_optimize_routes_no_vehicles(self, mock_get_vehicles, mock_session):
        """Test: Error cuando no hay vehículos disponibles"""
        # Mock distribution center
        mock_dc = Mock()
        mock_dc.id = 1
        mock_dc.latitude = Decimal('4.6097')
        mock_dc.longitude = Decimal('-74.0817')
        mock_session.get.return_value = mock_dc
        
        # No vehicles
        mock_get_vehicles.return_value = []
        
        orders = [{'id': 101, 'customer_name': 'Cliente 1'}]
        
        result = RouteOptimizerService.optimize_routes(
            orders=orders,
            distribution_center_id=1,
            planned_date=date(2025, 11, 20)
        )
        
        assert result['status'] == 'failed'
        assert any('vehículos' in str(e).lower() for e in result.get('errors', []))

    @patch('src.services.route_optimizer_service.Session')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._get_available_vehicles')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._geocode_orders')
    def test_optimize_routes_no_geocoded_orders(self, mock_geocode, mock_get_vehicles, mock_session):
        """Test: Error cuando no se puede geocodificar ninguna dirección"""
        # Mock distribution center
        mock_dc = Mock()
        mock_dc.id = 1
        mock_dc.latitude = Decimal('4.6097')
        mock_dc.longitude = Decimal('-74.0817')
        mock_session.get.return_value = mock_dc
        
        # Mock vehicles
        mock_vehicle = Mock()
        mock_vehicle.id = 1
        mock_get_vehicles.return_value = [mock_vehicle]
        
        # No geocoded orders
        mock_geocode.return_value = ([], ['Error geocodificando dirección'])
        
        orders = [{'id': 101, 'customer_name': 'Cliente 1', 'delivery_address': 'Dirección inválida'}]
        
        result = RouteOptimizerService.optimize_routes(
            orders=orders,
            distribution_center_id=1,
            planned_date=date(2025, 11, 20)
        )
        
        assert result['status'] == 'failed'
        assert any('geocodificar' in str(e).lower() for e in result.get('errors', []))


class TestRouteOptimizerServiceGeocoding:
    """Tests de geocodificación"""

    @patch('src.services.route_optimizer_service.get_google_maps_service')
    def test_geocode_orders_success(self, mock_gmaps_service):
        """Test: Geocodificar direcciones exitosamente"""
        mock_gmaps = Mock()
        mock_gmaps.geocode_address.return_value = {
            'lat': 4.6486259,  # Usar 'lat' no 'latitude'
            'lng': -74.0628451,  # Usar 'lng' no 'longitude'
            'formatted_address': 'Calle 50 #20-30, Bogotá'
        }
        mock_gmaps_service.return_value = mock_gmaps
        
        orders = [
            {
                'id': 101,
                'order_number': 'ORD-101',  # Requerido para logs
                'customer_name': 'Cliente 1',
                'delivery_address': 'Calle 50 #20-30',
                'city': 'Bogotá',
                'weight_kg': 50.0,
                'volume_m3': 1.0,
                'requires_cold_chain': False
            }
        ]
        
        geocoded, errors = RouteOptimizerService._geocode_orders(orders)
        
        assert len(geocoded) == 1
        assert geocoded[0]['latitude'] == 4.6486259
        assert geocoded[0]['longitude'] == -74.0628451
        assert len(errors) == 0

    @patch('src.services.route_optimizer_service.get_google_maps_service')
    def test_geocode_orders_already_geocoded(self, mock_gmaps_service):
        """Test: Órdenes ya geocodificadas no se vuelven a geocodificar"""
        mock_gmaps = Mock()
        mock_gmaps_service.return_value = mock_gmaps
        
        orders = [
            {
                'id': 101,
                'customer_name': 'Cliente 1',
                'delivery_address': 'Calle 50 #20-30',
                'latitude': 4.6486259,  # Ya geocodificado
                'longitude': -74.0628451,
                'weight_kg': 50.0,
                'volume_m3': 1.0,
                'requires_cold_chain': False
            }
        ]
        
        geocoded, errors = RouteOptimizerService._geocode_orders(orders)
        
        assert len(geocoded) == 1
        assert geocoded[0]['latitude'] == 4.6486259
        # No se llamó geocode_address porque ya tenía coordenadas
        mock_gmaps.geocode_address.assert_not_called()

    @patch('src.services.route_optimizer_service.get_google_maps_service')
    def test_geocode_orders_partial_failure(self, mock_gmaps_service):
        """Test: Algunas direcciones no se pueden geocodificar"""
        mock_gmaps = Mock()
        
        # La implementación real NO lanza excepciones, simplemente no agrega la orden si falla
        # Al revisar el código, si geocode_address falla, se captura el error
        def geocode_side_effect(address, city=None, department='', country='Colombia', use_cache=True):
            if 'inválida' in address:
                # Lanzar excepción para simular fallo
                raise Exception("Dirección no encontrada")
            return {
                'lat': 4.6486259,
                'lng': -74.0628451,
                'formatted_address': address
            }
        
        mock_gmaps.geocode_address.side_effect = geocode_side_effect
        mock_gmaps_service.return_value = mock_gmaps
        
        orders = [
            {
                'id': 101,
                'order_number': 'ORD-101',
                'customer_name': 'Cliente 1',
                'delivery_address': 'Dirección válida',
                'city': 'Bogotá',
                'weight_kg': 50.0,
                'volume_m3': 1.0,
                'requires_cold_chain': False
            },
            {
                'id': 102,
                'order_number': 'ORD-102',
                'customer_name': 'Cliente 2',
                'delivery_address': 'Dirección inválida',
                'city': 'Bogotá',
                'weight_kg': 30.0,
                'volume_m3': 0.5,
                'requires_cold_chain': False
            }
        ]
        
        geocoded, errors = RouteOptimizerService._geocode_orders(orders)
        
        # Solo una orden debe geocodificarse exitosamente
        assert len(geocoded) == 1
        assert geocoded[0]['id'] == 101
        # Debe haber errores registrados
        assert len(errors) > 0


class TestRouteOptimizerServiceDistanceMatrix:
    """Tests de cálculo de matriz de distancias"""

    @patch('src.services.route_optimizer_service.get_google_maps_service')
    def test_get_distance_matrix_success(self, mock_gmaps_service):
        """Test: Calcular matriz de distancias exitosamente"""
        mock_gmaps = Mock()
        # Usar las keys correctas que espera el código real
        mock_gmaps.get_distance_matrix.return_value = {
            'distances_km': [[0, 10, 15], [10, 0, 8], [15, 8, 0]],
            'durations_minutes': [[0, 15, 20], [15, 0, 12], [20, 12, 0]],
            'origins_count': 3,
            'destinations_count': 3
        }
        mock_gmaps_service.return_value = mock_gmaps
        
        coords = [
            (4.6097, -74.0817),  # depot
            (4.6486, -74.0628),  # order1
            (4.7040, -74.0314)   # order2
        ]
        
        distance_matrix, time_matrix, errors = RouteOptimizerService._get_distance_matrix(coords)
        
        assert len(distance_matrix) == 3
        assert len(time_matrix) == 3
        # Verificar que retorna la matriz del mock
        assert distance_matrix[0][1] == 10
        assert time_matrix[0][1] == 15
        assert len(errors) == 0

    @patch('src.services.route_optimizer_service.get_google_maps_service')
    def test_get_distance_matrix_error(self, mock_gmaps_service):
        """Test: Error al calcular matriz de distancias"""
        mock_gmaps = Mock()
        mock_gmaps.get_distance_matrix.side_effect = Exception("Google Maps API error")
        mock_gmaps_service.return_value = mock_gmaps
        
        coords = [(4.6097, -74.0817), (4.6486, -74.0628)]
        
        distance_matrix, time_matrix, errors = RouteOptimizerService._get_distance_matrix(coords)
        
        # Debe retornar matriz simple calculada con distancia euclidiana
        assert distance_matrix is not None
        assert len(errors) > 0


class TestRouteOptimizerServiceVehicles:
    """Tests de obtención de vehículos"""

    @patch('src.services.route_optimizer_service.Session')
    @patch('src.services.route_optimizer_service.Vehicle')
    def test_get_available_vehicles(self, mock_vehicle_model, mock_session_class):
        """Test: Obtener vehículos disponibles"""
        # Mock vehicles
        mock_vehicle1 = Mock()
        mock_vehicle1.id = 1
        mock_vehicle1.is_available = True
        
        mock_vehicle2 = Mock()
        mock_vehicle2.id = 2
        mock_vehicle2.is_available = True
        
        vehicles_list = [mock_vehicle1, mock_vehicle2]
        
        # Mock query chain
        mock_query = Mock()
        mock_filter_by = Mock()
        mock_filter_by.all.return_value = vehicles_list
        mock_query.filter_by.return_value = mock_filter_by
        
        # Mock Session (la clase, no instancia)
        mock_session_class.query.return_value = mock_query
        
        vehicles = RouteOptimizerService._get_available_vehicles(distribution_center_id=1)
        
        assert len(vehicles) == 2
        assert vehicles[0].id == 1


class TestRouteOptimizerServiceRouteCreation:
    """Tests de creación de objetos de ruta"""

    @patch('src.services.route_optimizer_service.Session')
    @patch('src.services.route_optimizer_service.DeliveryRoute')
    @patch('src.services.route_optimizer_service.RouteStop')
    @patch('src.services.route_optimizer_service.RouteAssignment')
    def test_create_route_objects_success(self, mock_assignment, mock_stop, mock_route_class, mock_session_class):
        """Test: Crear objetos de ruta - manejo de errores controlado"""
        solution = {
            'routes': [
                {
                    'vehicle_id': 1,
                    'stops': [
                        {'location_index': 0, 'order_id': None, 'sequence_order': 0, 'arrival_time_minutes': 0},
                        {'location_index': 1, 'order_id': 101, 'sequence_order': 1, 'arrival_time_minutes': 15},
                        {'location_index': 0, 'order_id': None, 'sequence_order': 2, 'arrival_time_minutes': 30}
                    ],
                    'total_distance_km': 20.0,
                    'total_time_minutes': 30,
                    'total_load_kg': 50.0,
                    'total_load_m3': 1.0,
                    'orders_count': 1
                }
            ],
            'optimization_score': 85.0
        }
        
        # Mock vehicles
        mock_vehicle = Mock()
        mock_vehicle.id = 1
        vehicles = [mock_vehicle]
        
        # Mock orders con campos m\u00ednimos (faltan campos intencionalmente para verificar manejo de errores)
        orders = [
            {
                'id': 101,
                'order_number': 'ORD-101'
            }
        ]
        
        # Mock distribution center
        mock_dc = Mock()
        mock_dc.id = 1
        
        # Mock query count para _generate_route_code
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.count.return_value = 0
        mock_query.filter.return_value = mock_filter
        mock_session_class.query.return_value = mock_query
        
        # Mock instancia de ruta
        mock_route_instance = Mock()
        mock_route_class.return_value = mock_route_instance
        
        routes, errors = RouteOptimizerService._create_route_objects(
            solution=solution,
            vehicles=vehicles,
            orders=orders,
            distribution_center=mock_dc,
            planned_date=date(2025, 11, 20),
            polyline=None
        )
        
        # Verificar que la función maneja errores sin crashear
        # Es esperado que haya errores ya que faltan campos en la orden
        assert isinstance(routes, list)
        assert isinstance(errors, list)
        # Debe haber registrado el error de campos faltantes
        assert len(errors) > 0


class TestRouteOptimizerServiceOptimizationStrategies:
    """Tests de diferentes estrategias de optimización"""

    @patch('src.services.route_optimizer_service.Session')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._get_available_vehicles')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._geocode_orders')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._get_distance_matrix')
    @patch('src.services.route_optimizer_service.RouteOptimizerService._create_route_objects')
    @patch('src.services.route_optimizer_service.VRPSolver')
    def test_optimize_strategy_minimize_distance(self, mock_solver_class, mock_create_routes, mock_matrix, mock_geocode, mock_vehicles, mock_session):
        """Test: Estrategia minimize_distance"""
        # Setup mocks
        self._setup_optimization_mocks(mock_session, mock_vehicles, mock_geocode, mock_matrix, mock_solver_class)
        
        # Mock create_route_objects
        mock_create_routes.return_value = ([], [])
        
        # Órdenes con todos los campos requeridos
        orders = [{
            'id': 101,
            'order_number': 'ORD-101',
            'customer_id': 1,
            'customer_name': 'C1',
            'delivery_address': 'Calle 1',
            'city': 'Bogotá',
            'weight_kg': 50,
            'volume_m3': 1,
            'requires_cold_chain': False,
            'clinical_priority': 3
        }]
        
        result = RouteOptimizerService.optimize_routes(
            orders=orders,
            distribution_center_id=1,
            planned_date=date(2025, 11, 20),
            optimization_strategy='minimize_distance'
        )
        
        # Verificar que se llamó solve
        mock_solver_instance = mock_solver_class.return_value
        assert mock_solver_instance.solve.called

    def _setup_optimization_mocks(self, mock_session, mock_vehicles, mock_geocode, mock_matrix, mock_solver_class):
        """Helper para configurar mocks comunes"""
        # Mock DC
        mock_dc = Mock()
        mock_dc.id = 1
        mock_dc.latitude = Decimal('4.6097')
        mock_dc.longitude = Decimal('-74.0817')
        mock_session.get.return_value = mock_dc
        
        # Mock vehicle
        mock_vehicle = Mock()
        mock_vehicle.id = 1
        mock_vehicle.capacity_kg = Decimal('1000')
        mock_vehicle.capacity_m3 = Decimal('10')
        mock_vehicle.has_refrigeration = False
        mock_vehicle.temperature_min = None
        mock_vehicle.temperature_max = None
        mock_vehicle.max_stops_per_route = 20
        mock_vehicle.cost_per_km = Decimal('2.5')
        mock_vehicle.avg_speed_kmh = Decimal('40')
        mock_vehicles.return_value = [mock_vehicle]
        
        # Mock geocoded orders con todos los campos necesarios
        mock_geocode.return_value = (
            [{
                'id': 101,
                'order_number': 'ORD-101',
                'customer_id': 1,
                'customer_name': 'C1',
                'delivery_address': 'Calle 1',
                'city': 'Bogotá',
                'latitude': 4.6486,
                'longitude': -74.0628,
                'weight_kg': 50,
                'volume_m3': 1,
                'requires_cold_chain': False,
                'clinical_priority': 3
            }],
            []
        )
        
        # Mock matrix
        mock_matrix.return_value = (
            [[0, 10], [10, 0]],
            [[0, 15], [15, 0]],
            []
        )
        
        # Mock solver
        mock_solver_instance = Mock()
        mock_solver_instance.solve.return_value = {
            'status': 'success',
            'routes': [],
            'unassigned_orders': [],
            'total_distance_km': 20.0,
            'total_time_minutes': 30,
            'total_cost': 50.0,
            'optimization_score': 85.0
        }
        mock_solver_class.return_value = mock_solver_instance
