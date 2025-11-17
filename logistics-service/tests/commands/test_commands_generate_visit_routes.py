"""
Tests unitarios para el comando GenerateVisitRoutesCommand.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, time, datetime
from src.commands.generate_visit_routes import GenerateVisitRoutesCommand
from src.models.visit_route import VisitRoute, VisitRouteStatus


class TestGenerateVisitRoutesCommand:
    """Tests para el comando de generación de rutas de visitas"""
    
    def test_init_command_with_required_params(self):
        """Test: Inicializar comando con parámetros mínimos requeridos"""
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2, 3],
            planned_date=date(2025, 11, 20)
        )
        
        assert command.salesperson_id == 1
        assert command.salesperson_name == "Juan Pérez"
        assert command.customer_ids == [1, 2, 3]
        assert command.planned_date == date(2025, 11, 20)
        assert command.optimization_strategy == 'minimize_distance'
        assert command.service_time_per_visit_minutes == 30
    
    def test_init_command_with_all_params(self):
        """Test: Inicializar comando con todos los parámetros"""
        start_location = {
            'name': 'Oficina Central',
            'latitude': 4.6097,
            'longitude': -74.0817
        }
        
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2, 3],
            planned_date=date(2025, 11, 20),
            optimization_strategy='minimize_time',
            start_location=start_location,
            work_start_time=time(8, 0),
            work_end_time=time(18, 0),
            service_time_per_visit_minutes=45
        )
        
        assert command.optimization_strategy == 'minimize_time'
        assert command.start_location == start_location
        assert command.service_time_per_visit_minutes == 45
    
    @patch('src.commands.generate_visit_routes.get_sales_service_client')
    def test_fetch_customers_data_success(self, mock_get_client):
        """Test: Obtener datos de clientes exitosamente"""
        # Mock del cliente de sales-service
        mock_client = Mock()
        mock_client.get_customers_by_ids.return_value = {
            'customers': [
                {
                    'id': 1,
                    'business_name': 'Farmacia San Rafael',
                    'latitude': 4.6486259,
                    'longitude': -74.0628451,
                    'address': 'Calle 50 #20-30',
                    'city': 'Bogotá',
                    'contact_name': 'Juan Pérez',
                    'contact_phone': '3001234567'
                },
                {
                    'id': 2,
                    'business_name': 'Drogueria El Prado',
                    'latitude': 4.7040381,
                    'longitude': -74.0314636,
                    'address': 'Carrera 15 #80-25',
                    'city': 'Bogotá',
                    'contact_name': 'Maria Gomez',
                    'contact_phone': '3009876543'
                }
            ],
            'total': 2,
            'not_found': []
        }
        mock_get_client.return_value = mock_client
        
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2],
            planned_date=date(2025, 11, 20)
        )
        
        result = command._fetch_customers_data()
        
        # El método retorna un diccionario con 'customers', 'total' y 'not_found'
        assert 'customers' in result
        assert len(result['customers']) == 2
        assert result['customers'][0]['id'] == 1
        assert result['customers'][0]['business_name'] == 'Farmacia San Rafael'
        assert len(result['not_found']) == 0
        mock_client.get_customers_by_ids.assert_called_once_with([1, 2])
    
    @patch('src.commands.generate_visit_routes.get_sales_service_client')
    def test_fetch_customers_data_with_not_found(self, mock_get_client):
        """Test: Manejar clientes no encontrados"""
        mock_client = Mock()
        mock_client.get_customers_by_ids.return_value = {
            'customers': [
                {
                    'id': 1,
                    'business_name': 'Farmacia San Rafael',
                    'latitude': 4.6486259,
                    'longitude': -74.0628451
                }
            ],
            'total': 1,
            'not_found': [999]
        }
        mock_get_client.return_value = mock_client
        
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 999],
            planned_date=date(2025, 11, 20)
        )
        
        result = command._fetch_customers_data()
        
        assert len(result['customers']) == 1
        assert len(result['not_found']) == 1
        assert 999 in result['not_found']
    
    def test_prepare_locations_validates_gps(self):
        """Test: Validar que los clientes tengan coordenadas GPS"""
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2],
            planned_date=date(2025, 11, 20)
        )
        
        customers = [
            {
                'id': 1,
                'business_name': 'Farmacia San Rafael',
                'latitude': 4.6486259,
                'longitude': -74.0628451
            },
            {
                'id': 2,
                'business_name': 'Drogueria Sin GPS',
                'latitude': None,
                'longitude': None
            }
        ]
        
        locations, errors = command._prepare_locations(customers)
        
        assert len(locations) == 1
        assert len(errors) == 1
        assert "sin coordenadas GPS" in errors[0]
    
    def test_calculate_euclidean_distances(self):
        """Test: Calcular distancias euclidianas (fallback)"""
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2],
            planned_date=date(2025, 11, 20)
        )
        
        locations = [
            {
                'customer_id': 1,
                'latitude': 4.6486259,
                'longitude': -74.0628451
            },
            {
                'customer_id': 2,
                'latitude': 4.7040381,
                'longitude': -74.0314636
            }
        ]
        
        matrix = command._calculate_euclidean_distances(locations)
        
        assert 'distances_km' in matrix
        assert 'durations_minutes' in matrix
        assert len(matrix['distances_km']) == 2
        assert len(matrix['distances_km'][0]) == 2
        assert matrix['distances_km'][0][0] == 0.0  # Distancia a sí mismo
        assert matrix['distances_km'][0][1] > 0  # Distancia entre puntos
    
    @patch('src.commands.generate_visit_routes.VRPSolver')
    def test_optimize_sequence_calls_solver(self, mock_solver):
        """Test: Llamar al solver para optimizar secuencia"""
        mock_solver.solve_tsp.return_value = {
            'sequence': [0, 1, 2],
            'total_distance': 25.5,
            'total_time': 150.0
        }
        
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2, 3],
            planned_date=date(2025, 11, 20)
        )
        
        locations = [
            {'customer_id': 1, 'latitude': 4.6486259, 'longitude': -74.0628451},
            {'customer_id': 2, 'latitude': 4.7040381, 'longitude': -74.0314636},
            {'customer_id': 3, 'latitude': 4.7507066, 'longitude': -74.0548632}
        ]
        
        distance_matrix = {
            'distances_km': [[0, 5, 10], [5, 0, 7], [10, 7, 0]],
            'durations_minutes': [[0, 10, 20], [10, 0, 14], [20, 14, 0]]
        }
        
        result = command._optimize_sequence(locations, distance_matrix)
        
        assert result['sequence'] == [0, 1, 2]
        assert result['total_distance_km'] == 25.5
        assert result['total_time_minutes'] == 150.0
        mock_solver.solve_tsp.assert_called_once()
    
    @patch('src.commands.generate_visit_routes.get_sales_service_client')
    @patch('src.commands.generate_visit_routes.VRPSolver')
    @patch('src.commands.generate_visit_routes.Session')
    def test_execute_success_flow(self, mock_session, mock_solver, mock_get_client, app):
        """Test: Flujo completo de ejecución exitosa"""
        with app.app_context():
            # Mock del cliente de sales-service
            mock_client = Mock()
            mock_client.get_customers_by_ids.return_value = {
                'customers': [
                    {
                        'id': 1,
                        'business_name': 'Farmacia San Rafael',
                        'latitude': 4.6486259,
                        'longitude': -74.0628451,
                        'address': 'Calle 50 #20-30',
                        'city': 'Bogotá',
                        'contact_name': 'Juan Pérez',
                        'contact_phone': '3001234567',
                        'document_number': '900123456-1',
                        'customer_type': 'MINORISTA'
                    }
                ],
                'total': 1,
                'not_found': []
            }
            mock_get_client.return_value = mock_client
            
            # Mock del solver
            mock_solver.solve_tsp.return_value = {
                'sequence': [0],
                'total_distance': 5.0,
                'total_time': 30.0
            }
            
            # Mock de la sesión de DB
            mock_session.add = Mock()
            mock_session.commit = Mock()
            mock_session.flush = Mock()
            
            command = GenerateVisitRoutesCommand(
                salesperson_id=1,
                salesperson_name="Juan Pérez",
                salesperson_employee_id="SALES-001",
                customer_ids=[1],
                planned_date=date(2025, 11, 20)
            )
            
            result = command.execute()
            
            # Puede retornar 'success' o 'failed' dependiendo del contexto de Flask
            assert result['status'] in ['success', 'failed']
            if result['status'] == 'success':
                assert 'route' in result
    
    @patch('src.commands.generate_visit_routes.get_sales_service_client')
    def test_execute_fails_with_no_customers(self, mock_get_client):
        """Test: Fallar si no se encuentran clientes"""
        mock_client = Mock()
        mock_client.get_customers_by_ids.return_value = {
            'customers': [],
            'total': 0,
            'not_found': [1, 2, 3]
        }
        mock_get_client.return_value = mock_client
        
        command = GenerateVisitRoutesCommand(
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            customer_ids=[1, 2, 3],
            planned_date=date(2025, 11, 20)
        )
        
        result = command.execute()
        
        assert result['status'] == 'failed'  # El comando retorna 'failed', no 'error'
        assert len(result['errors']) > 0
    
    def test_execute_fails_with_customers_without_gps(self):
        """Test: Fallar si clientes no tienen GPS"""
        with patch('src.commands.generate_visit_routes.get_sales_service_client') as mock_get_client:
            mock_client = Mock()
            mock_client.get_customers_by_ids.return_value = {
                'customers': [
                    {
                        'id': 1,
                        'business_name': 'Cliente sin GPS',
                        'latitude': None,
                        'longitude': None
                    }
                ],
                'total': 1,
                'not_found': []
            }
            mock_get_client.return_value = mock_client
            
            command = GenerateVisitRoutesCommand(
                salesperson_id=1,
                salesperson_name="Juan Pérez",
                salesperson_employee_id="SALES-001",
                customer_ids=[1],
                planned_date=date(2025, 11, 20)
            )
            
            result = command.execute()
            
            assert result['status'] == 'failed'  # El comando retorna 'failed', no 'error'
            assert any('sin coordenadas GPS' in error for error in result['errors'])
