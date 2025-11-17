"""
Tests para utils/vrp_solver.py

Coverage objetivo: >80%

Funcionalidad a probar:
- Inicialización y validaciones
- Solución básica del VRP
- Callbacks de distancia y tiempo
- Restricciones de capacidad (peso y volumen)
- Restricciones de cadena de frío
- Penalizaciones por prioridad
- Extracción de solución
"""

import pytest
from datetime import time
from unittest.mock import Mock, patch, MagicMock

from src.utils.vrp_solver import VRPSolver


class TestVRPSolverInitialization:
    """Tests de inicialización del VRPSolver"""

    def test_init_basic(self):
        """Test: Inicialización básica del solver"""
        vehicles = [
            {
                'id': 1,
                'capacity_kg': 1000.0,
                'capacity_m3': 10.0,
                'has_refrigeration': False,
                'max_stops': 20,
                'cost_per_km': 2.5,
                'avg_speed_kmh': 40.0
            }
        ]
        
        orders = [
            {
                'id': 101,
                'customer_name': 'Cliente 1',
                'address': 'Calle 1',
                'latitude': 4.6097,
                'longitude': -74.0817,
                'weight_kg': 50.0,
                'volume_m3': 1.0,
                'requires_cold_chain': False,
                'clinical_priority': 3,
                'service_time_minutes': 15
            }
        ]
        
        # Matriz 2x2: [depot, order1]
        distance_matrix = [
            [0, 10],    # desde depot
            [10, 0]     # desde order1
        ]
        
        time_matrix = [
            [0, 15],
            [15, 0]
        ]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix,
            depot_index=0
        )
        
        assert solver.num_vehicles == 1
        assert solver.num_locations == 2
        assert solver.depot_index == 0
        assert len(solver.orders) == 1

    def test_init_validation_matrix_size_mismatch(self):
        """Test: Validar que matriz de distancias coincida con número de pedidos"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        
        # Matriz incorrecta (3x3 para 1 pedido)
        distance_matrix = [[0, 10, 5], [10, 0, 8], [5, 8, 0]]
        time_matrix = [[0, 15, 10], [15, 0, 12], [10, 12, 0]]
        
        with pytest.raises(ValueError, match="matriz de distancias"):
            VRPSolver(
                vehicles=vehicles,
                orders=orders,
                distance_matrix_km=distance_matrix,
                time_matrix_minutes=time_matrix
            )

    def test_init_validation_no_vehicles(self):
        """Test: Validar que haya al menos un vehículo"""
        vehicles = []
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 15], [15, 0]]
        
        with pytest.raises(ValueError, match="No hay vehículos"):
            VRPSolver(
                vehicles=vehicles,
                orders=orders,
                distance_matrix_km=distance_matrix,
                time_matrix_minutes=time_matrix
            )

    def test_init_validation_no_orders(self):
        """Test: Validar que haya al menos un pedido"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = []
        distance_matrix = [[0]]
        time_matrix = [[0]]
        
        with pytest.raises(ValueError, match="No hay pedidos"):
            VRPSolver(
                vehicles=vehicles,
                orders=orders,
                distance_matrix_km=distance_matrix,
                time_matrix_minutes=time_matrix
            )

    def test_init_validation_time_distance_mismatch(self):
        """Test: Validar que matrices de tiempo y distancia tengan mismas dimensiones"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 15, 20], [15, 0, 18], [20, 18, 0]]  # Diferente dimensión
        
        with pytest.raises(ValueError, match="dimensiones diferentes"):
            VRPSolver(
                vehicles=vehicles,
                orders=orders,
                distance_matrix_km=distance_matrix,
                time_matrix_minutes=time_matrix
            )


class TestVRPSolverCallbacks:
    """Tests de callbacks de distancia y tiempo"""

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_register_distance_callback(self, mock_ortools):
        """Test: Registrar callback de distancia"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        distance_matrix = [[0, 10.5], [10.5, 0]]
        time_matrix = [[0, 15], [15, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        # Mock manager
        mock_manager = Mock()
        mock_manager.IndexToNode.side_effect = lambda x: x
        
        # Mock routing
        mock_routing = Mock()
        mock_routing.RegisterTransitCallback.return_value = 123
        
        result = solver._register_distance_callback(mock_manager, mock_routing)
        
        assert result == 123
        mock_routing.RegisterTransitCallback.assert_called_once()

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_register_time_callback(self, mock_ortools):
        """Test: Registrar callback de tiempo"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 20.5], [20.5, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        mock_manager = Mock()
        mock_manager.IndexToNode.side_effect = lambda x: x
        
        mock_routing = Mock()
        mock_routing.RegisterTransitCallback.return_value = 456
        
        result = solver._register_time_callback(mock_manager, mock_routing)
        
        assert result == 456
        mock_routing.RegisterTransitCallback.assert_called_once()


class TestVRPSolverCapacityDimensions:
    """Tests de restricciones de capacidad"""

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_add_capacity_dimension_weight(self, mock_ortools):
        """Test: Agregar dimensión de capacidad de peso"""
        vehicles = [
            {'id': 1, 'capacity_kg': 1000.0, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40},
            {'id': 2, 'capacity_kg': 500.0, 'capacity_m3': 5, 'has_refrigeration': False, 'max_stops': 15, 'cost_per_km': 2.0, 'avg_speed_kmh': 35}
        ]
        orders = [
            {'id': 101, 'weight_kg': 50.0, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15},
            {'id': 102, 'weight_kg': 75.0, 'volume_m3': 1.5, 'requires_cold_chain': False, 'clinical_priority': 2, 'service_time_minutes': 20}
        ]
        distance_matrix = [[0, 10, 15], [10, 0, 8], [15, 8, 0]]
        time_matrix = [[0, 15, 20], [15, 0, 12], [20, 12, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        mock_manager = Mock()
        mock_manager.IndexToNode.side_effect = lambda x: x
        
        mock_routing = Mock()
        mock_routing.RegisterUnaryTransitCallback.return_value = 789
        
        solver._add_capacity_dimension_weight(mock_manager, mock_routing)
        
        mock_routing.RegisterUnaryTransitCallback.assert_called_once()
        mock_routing.AddDimensionWithVehicleCapacity.assert_called_once()

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_add_capacity_dimension_volume(self, mock_ortools):
        """Test: Agregar dimensión de capacidad de volumen"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10.0, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 2.5, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 15], [15, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        mock_manager = Mock()
        mock_manager.IndexToNode.side_effect = lambda x: x
        
        mock_routing = Mock()
        mock_routing.RegisterUnaryTransitCallback.return_value = 999
        
        solver._add_capacity_dimension_volume(mock_manager, mock_routing)
        
        mock_routing.RegisterUnaryTransitCallback.assert_called_once()
        mock_routing.AddDimensionWithVehicleCapacity.assert_called_once()


class TestVRPSolverConstraints:
    """Tests de restricciones adicionales"""

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_cold_chain_constraints(self, mock_ortools):
        """Test: Restricciones de cadena de frío"""
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': True, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40},
            {'id': 2, 'capacity_kg': 500, 'capacity_m3': 5, 'has_refrigeration': False, 'max_stops': 15, 'cost_per_km': 2.0, 'avg_speed_kmh': 35}
        ]
        orders = [
            {'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': True, 'clinical_priority': 1, 'service_time_minutes': 15},
            {'id': 102, 'weight_kg': 30, 'volume_m3': 0.5, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 10}
        ]
        distance_matrix = [[0, 10, 15], [10, 0, 8], [15, 8, 0]]
        time_matrix = [[0, 15, 20], [15, 0, 12], [20, 12, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        mock_manager = Mock()
        mock_routing = Mock()
        
        # Verificar que no lance excepción
        solver._add_cold_chain_constraints(mock_manager, mock_routing)

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_max_stops_constraint(self, mock_ortools):
        """Test: Restricción de máximo de paradas"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 5, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 15], [15, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        mock_routing = Mock()
        
        solver._add_max_stops_constraint(mock_routing)
        
        # Verificar que se llamó AddConstantDimensionWithSlack o similar
        # (depende de implementación interna de OR-Tools)
        assert mock_routing.method_calls  # Verificar que se llamó algún método


class TestVRPSolverSolve:
    """Tests del método solve"""

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_solve_no_solution(self, mock_ortools):
        """Test: Cuando no hay solución factible"""
        vehicles = [{'id': 1, 'capacity_kg': 10, 'capacity_m3': 0.1, 'has_refrigeration': False, 'max_stops': 1, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [
            {'id': 101, 'weight_kg': 500, 'volume_m3': 50, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}
        ]
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 15], [15, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        # Mock OR-Tools para que no encuentre solución
        mock_manager = Mock()
        mock_routing = Mock()
        mock_routing.SolveWithParameters.return_value = None
        
        mock_ortools.RoutingIndexManager.return_value = mock_manager
        mock_ortools.RoutingModel.return_value = mock_routing
        
        result = solver.solve()
        
        assert result['status'] == 'failed'
        assert len(result['routes']) == 0
        assert len(result['unassigned_orders']) == 1
        assert result['unassigned_orders'][0] == 101

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_solve_exception_handling(self, mock_ortools):
        """Test: Manejo de excepciones durante solve"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [{'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15}]
        distance_matrix = [[0, 10], [10, 0]]
        time_matrix = [[0, 15], [15, 0]]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        # Mock que lanza excepción
        mock_ortools.RoutingIndexManager.side_effect = Exception("OR-Tools error")
        
        result = solver.solve()
        
        assert result['status'] == 'failed'
        assert 'error' in result
        assert 'OR-Tools error' in result['error']


class TestVRPSolverTSP:
    """Tests del método solve_tsp (Traveling Salesman Problem)"""

    @patch('src.utils.vrp_solver.pywrapcp')
    def test_solve_tsp_basic(self, mock_ortools):
        """Test: Resolver TSP básico con un solo vehículo"""
        vehicles = [{'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'has_refrigeration': False, 'max_stops': 20, 'cost_per_km': 2.5, 'avg_speed_kmh': 40}]
        orders = [
            {'id': 101, 'weight_kg': 50, 'volume_m3': 1, 'requires_cold_chain': False, 'clinical_priority': 3, 'service_time_minutes': 15},
            {'id': 102, 'weight_kg': 30, 'volume_m3': 0.5, 'requires_cold_chain': False, 'clinical_priority': 2, 'service_time_minutes': 10}
        ]
        distance_matrix = [
            [0, 10, 15],
            [10, 0, 8],
            [15, 8, 0]
        ]
        time_matrix = [
            [0, 15, 20],
            [15, 0, 12],
            [20, 12, 0]
        ]
        
        solver = VRPSolver(
            vehicles=vehicles,
            orders=orders,
            distance_matrix_km=distance_matrix,
            time_matrix_minutes=time_matrix
        )
        
        # Verificar que el método existe
        assert hasattr(solver, 'solve_tsp')
