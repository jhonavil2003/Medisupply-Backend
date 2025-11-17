"""
Tests unitarios para validadores de rutas.
"""

import pytest
from src.utils.route_validators import RouteValidator


class TestRouteValidator:
    """Tests para RouteValidator"""
    
    def test_validate_solution_failed_status(self):
        """Test: Validar solución con status failed"""
        solution = {
            'status': 'failed',
            'routes': []
        }
        
        result = RouteValidator.validate_solution(
            solution=solution,
            vehicles=[],
            orders=[]
        )
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert any('falló' in error for error in result['errors'])
    
    def test_validate_solution_no_routes_generated(self):
        """Test: Validar solución sin rutas generadas"""
        solution = {
            'status': 'success',
            'routes': []
        }
        
        result = RouteValidator.validate_solution(
            solution=solution,
            vehicles=[],
            orders=[]
        )
        
        assert result['is_valid'] is False
        assert any('No se generaron rutas' in error for error in result['errors'])
    
    def test_validate_solution_with_unassigned_orders(self):
        """Test: Validar solución con pedidos sin asignar"""
        solution = {
            'status': 'success',
            'routes': [
                {
                    'vehicle_id': 1,
                    'stops': [
                        {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                        {'location_index': 1, 'sequence_order': 1, 'order_id': 101},
                        {'location_index': 0, 'sequence_order': 2, 'order_id': None}
                    ],
                    'total_load_kg': 10.0,
                    'total_load_m3': 0.5,
                    'total_distance_km': 20.0,
                    'total_time_minutes': 60
                }
            ],
            'unassigned_orders': [102, 103]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        orders = [
            {'id': 101},
            {'id': 102},
            {'id': 103}
        ]
        
        result = RouteValidator.validate_solution(
            solution=solution,
            vehicles=vehicles,
            orders=orders
        )
        
        # Debe ser válido pero con warnings
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0
        assert any('sin asignar' in warning for warning in result['warnings'])
    
    def test_validate_solution_duplicate_orders(self):
        """Test: Detectar pedidos duplicados en múltiples rutas"""
        solution = {
            'status': 'success',
            'routes': [
                {
                    'vehicle_id': 1,
                    'stops': [
                        {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                        {'location_index': 1, 'sequence_order': 1, 'order_id': 101},
                        {'location_index': 0, 'sequence_order': 2, 'order_id': None}
                    ],
                    'total_load_kg': 10.0,
                    'total_load_m3': 0.5,
                    'total_distance_km': 20.0,
                    'total_time_minutes': 60
                },
                {
                    'vehicle_id': 2,
                    'stops': [
                        {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                        {'location_index': 1, 'sequence_order': 1, 'order_id': 101},  # Duplicado
                        {'location_index': 0, 'sequence_order': 2, 'order_id': None}
                    ],
                    'total_load_kg': 10.0,
                    'total_load_m3': 0.5,
                    'total_distance_km': 20.0,
                    'total_time_minutes': 60
                }
            ],
            'unassigned_orders': []
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20},
            {'id': 2, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        orders = [{'id': 101}]
        
        result = RouteValidator.validate_solution(
            solution=solution,
            vehicles=vehicles,
            orders=orders
        )
        
        assert result['is_valid'] is False
        assert any('asignado a múltiples rutas' in error for error in result['errors'])
    
    def test_validate_solution_nonexistent_order(self):
        """Test: Detectar pedido inexistente en ruta"""
        solution = {
            'status': 'success',
            'routes': [
                {
                    'vehicle_id': 1,
                    'stops': [
                        {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                        {'location_index': 1, 'sequence_order': 1, 'order_id': 999},  # No existe
                        {'location_index': 0, 'sequence_order': 2, 'order_id': None}
                    ],
                    'total_load_kg': 10.0,
                    'total_load_m3': 0.5,
                    'total_distance_km': 20.0,
                    'total_time_minutes': 60
                }
            ],
            'unassigned_orders': []
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        orders = [{'id': 101}]
        
        result = RouteValidator.validate_solution(
            solution=solution,
            vehicles=vehicles,
            orders=orders
        )
        
        assert result['is_valid'] is False
        assert any('inexistente' in error for error in result['errors'])
    
    def test_validate_single_route_weight_overload(self):
        """Test: Detectar sobrecarga de peso"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 1500.0,  # Sobrecarga
            'total_load_m3': 5.0,
            'total_distance_km': 50.0,
            'total_time_minutes': 120,
            'stops': [
                {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                {'location_index': 1, 'sequence_order': 1, 'order_id': 101},
                {'location_index': 0, 'sequence_order': 2, 'order_id': None}
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('Sobrecarga de peso' in error for error in errors)
    
    def test_validate_single_route_volume_overload(self):
        """Test: Detectar sobrecarga de volumen"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 15.0,  # Sobrecarga de volumen
            'total_distance_km': 50.0,
            'total_time_minutes': 120,
            'stops': [
                {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                {'location_index': 1, 'sequence_order': 1, 'order_id': 101},
                {'location_index': 0, 'sequence_order': 2, 'order_id': None}
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('Sobrecarga de volumen' in error for error in errors)
    
    def test_validate_single_route_distance_exceeded(self):
        """Test: Detectar exceso de distancia"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 5.0,
            'total_distance_km': 350.0,  # Excede límite
            'total_time_minutes': 120,
            'stops': [
                {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                {'location_index': 1, 'sequence_order': 1, 'order_id': 101},
                {'location_index': 0, 'sequence_order': 2, 'order_id': None}
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('Distancia excesiva' in error for error in errors)
    
    def test_validate_single_route_time_exceeded(self):
        """Test: Detectar exceso de tiempo"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 5.0,
            'total_distance_km': 200.0,
            'total_time_minutes': 700,  # Excede límite
            'stops': [
                {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                {'location_index': 1, 'sequence_order': 1, 'order_id': 101},
                {'location_index': 0, 'sequence_order': 2, 'order_id': None}
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('Tiempo excesivo' in error for error in errors)
    
    def test_validate_single_route_too_many_stops(self):
        """Test: Detectar demasiadas paradas"""
        # Crear 25 paradas (excede máximo de 20)
        stops = [{'location_index': 0, 'sequence_order': 0, 'order_id': None}]
        for i in range(1, 25):
            stops.append({'location_index': i, 'sequence_order': i, 'order_id': 100 + i})
        stops.append({'location_index': 0, 'sequence_order': 25, 'order_id': None})
        
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 5.0,
            'total_distance_km': 200.0,
            'total_time_minutes': 300,
            'stops': stops
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('Demasiadas paradas' in error for error in errors)
    
    def test_validate_single_route_not_starting_at_depot(self):
        """Test: Ruta no comienza en depot"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 5.0,
            'total_distance_km': 50.0,
            'total_time_minutes': 120,
            'stops': [
                {'location_index': 1, 'sequence_order': 0, 'order_id': 101},  # No comienza en 0
                {'location_index': 0, 'sequence_order': 1, 'order_id': None}
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('No comienza en depot' in error for error in errors)
    
    def test_validate_single_route_not_ending_at_depot(self):
        """Test: Ruta no termina en depot"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 5.0,
            'total_distance_km': 50.0,
            'total_time_minutes': 120,
            'stops': [
                {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                {'location_index': 1, 'sequence_order': 1, 'order_id': 101}  # No termina en 0
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('No termina en depot' in error for error in errors)
    
    def test_validate_single_route_invalid_sequence(self):
        """Test: Secuencia de paradas incorrecta"""
        route = {
            'vehicle_id': 1,
            'total_load_kg': 500.0,
            'total_load_m3': 5.0,
            'total_distance_km': 50.0,
            'total_time_minutes': 120,
            'stops': [
                {'location_index': 0, 'sequence_order': 0, 'order_id': None},
                {'location_index': 1, 'sequence_order': 5, 'order_id': 101},  # Salto en secuencia
                {'location_index': 0, 'sequence_order': 2, 'order_id': None}
            ]
        }
        
        vehicles = [
            {'id': 1, 'capacity_kg': 1000, 'capacity_m3': 10, 'max_stops': 20}
        ]
        
        errors, warnings = RouteValidator._validate_single_route(
            route=route,
            vehicles=vehicles,
            orders=[],
            route_number=1,
            max_distance_km=300,
            max_time_minutes=600
        )
        
        assert len(errors) > 0
        assert any('Secuencia incorrecta' in error for error in errors)
    
    def test_validate_route_reassignment_success(self):
        """Test: Validar reasignación válida"""
        vehicles = [
            {'id': 10, 'is_available': True, 'plate': 'ABC-123'}
        ]
        
        result = RouteValidator.validate_route_reassignment(
            order_id=101,
            current_route_id=1,
            new_vehicle_id=10,
            vehicles=vehicles,
            reason='Vehículo original con falla mecánica'
        )
        
        assert result['is_valid'] is True
        assert len(result['errors']) == 0
    
    def test_validate_route_reassignment_vehicle_not_found(self):
        """Test: Reasignación a vehículo inexistente"""
        vehicles = [
            {'id': 10, 'is_available': True}
        ]
        
        result = RouteValidator.validate_route_reassignment(
            order_id=101,
            current_route_id=1,
            new_vehicle_id=999,  # No existe
            vehicles=vehicles,
            reason='Test'
        )
        
        assert result['is_valid'] is False
        assert any('no encontrado' in error for error in result['errors'])
    
    def test_validate_route_reassignment_vehicle_unavailable(self):
        """Test: Reasignación a vehículo no disponible"""
        vehicles = [
            {'id': 10, 'is_available': False}
        ]
        
        result = RouteValidator.validate_route_reassignment(
            order_id=101,
            current_route_id=1,
            new_vehicle_id=10,
            vehicles=vehicles,
            reason='Test'
        )
        
        assert result['is_valid'] is False
        assert any('no está disponible' in error for error in result['errors'])
    
    def test_validate_route_reassignment_invalid_reason(self):
        """Test: Reasignación sin motivo válido"""
        vehicles = [
            {'id': 10, 'is_available': True}
        ]
        
        result = RouteValidator.validate_route_reassignment(
            order_id=101,
            current_route_id=1,
            new_vehicle_id=10,
            vehicles=vehicles,
            reason='abc'  # Muy corto
        )
        
        assert result['is_valid'] is False
        assert any('motivo válido' in error for error in result['errors'])
    
    def test_validate_route_reassignment_urgent_warning(self):
        """Test: Warning para reasignación urgente"""
        vehicles = [
            {'id': 10, 'is_available': True}
        ]
        
        result = RouteValidator.validate_route_reassignment(
            order_id=101,
            current_route_id=1,
            new_vehicle_id=10,
            vehicles=vehicles,
            reason='Emergencia: vehículo con avería crítica'
        )
        
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0
        assert any('urgente' in warning.lower() for warning in result['warnings'])
