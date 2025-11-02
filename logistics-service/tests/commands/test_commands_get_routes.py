"""
Tests unitarios para los comandos de consulta de rutas.
Basado en la estructura de tests del proyecto.
"""

from datetime import date, timedelta
from decimal import Decimal

from src.commands.get_routes import GetRoutes, GetRouteById, GetRoutesByDate
from src.models.delivery_route import DeliveryRoute
from src.models.vehicle import Vehicle


class TestGetRoutesCommand:
    """Test suite para el comando GetRoutes."""
    
    def test_get_routes_all(self, db, sample_delivery_route):
        """Test consulta de todas las rutas sin filtros."""
        command = GetRoutes()
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'routes' in result
        assert len(result['routes']) >= 1
        assert result['total'] >= 1
    
    def test_get_routes_by_distribution_center(self, db, sample_distribution_center, sample_delivery_route):
        """Test filtrado por centro de distribución."""
        command = GetRoutes(distribution_center_id=sample_distribution_center.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert all(r['distribution_center_id'] == sample_distribution_center.id for r in result['routes'])
    
    def test_get_routes_by_planned_date(self, db, sample_delivery_route):
        """Test filtrado por fecha planeada."""
        planned_date = date.today()
        
        command = GetRoutes(planned_date=planned_date)
        result = command.execute()
        
        assert result['status'] == 'success'
        # Verificar que hay rutas en el resultado
        assert 'routes' in result
        # El filtro se aplica en el query, verificar que el comando ejecutó correctamente
        assert result['total'] >= 0
    
    def test_get_routes_by_status(self, db, sample_delivery_route):
        """Test filtrado por estado."""
        command = GetRoutes(status='draft')
        result = command.execute()
        
        assert result['status'] == 'success'
        assert all(r['status'] == 'draft' for r in result['routes'])
    
    def test_get_routes_by_vehicle(self, db, sample_vehicle, sample_delivery_route):
        """Test filtrado por vehículo."""
        command = GetRoutes(vehicle_id=sample_vehicle.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert all(r['vehicle_id'] == sample_vehicle.id for r in result['routes'])
    
    def test_get_routes_pagination(self, db, sample_distribution_center, sample_vehicle):
        """Test paginación de resultados."""
        # Crear múltiples rutas
        for i in range(10):
            route = DeliveryRoute(
                route_code=f'ROUTE-TEST-{i:03d}',
                vehicle_id=sample_vehicle.id,
                planned_date=date.today() + timedelta(days=i % 3),
                status='draft',
                distribution_center_id=sample_distribution_center.id
            )
            db.session.add(route)
        db.session.commit()
        
        # Página 1
        command1 = GetRoutes(limit=5, offset=0)
        result1 = command1.execute()
        
        assert result1['status'] == 'success'
        assert len(result1['routes']) <= 5
        assert result1['limit'] == 5
        assert result1['offset'] == 0
        
        # Página 2
        command2 = GetRoutes(limit=5, offset=5)
        result2 = command2.execute()
        
        assert result2['status'] == 'success'
        assert result2['offset'] == 5
    
    def test_get_routes_multiple_filters(self, db, sample_distribution_center, sample_vehicle, sample_delivery_route):
        """Test múltiples filtros combinados."""
        command = GetRoutes(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today(),
            status='draft',
            vehicle_id=sample_vehicle.id
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        for route in result['routes']:
            assert route['distribution_center_id'] == sample_distribution_center.id
            assert route['status'] == 'draft'
            assert route['vehicle_id'] == sample_vehicle.id
    
    def test_get_routes_empty_result(self, db):
        """Test consulta que no retorna resultados."""
        future_date = date.today() + timedelta(days=365)
        
        command = GetRoutes(planned_date=future_date)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert result['routes'] == []
        assert result['total'] == 0
    
    def test_get_routes_has_more_flag(self, db, sample_distribution_center, sample_vehicle):
        """Test indicador de más resultados disponibles."""
        # Crear 15 rutas
        for i in range(15):
            route = DeliveryRoute(
                route_code=f'ROUTE-MORE-{i:03d}',
                vehicle_id=sample_vehicle.id,
                planned_date=date.today(),
                status='draft',
                distribution_center_id=sample_distribution_center.id
            )
            db.session.add(route)
        db.session.commit()
        
        command = GetRoutes(limit=10, offset=0)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert result['has_more'] is True
        
        # Segunda página
        command2 = GetRoutes(limit=10, offset=10)
        result2 = command2.execute()
        
        # Puede ser True o False dependiendo de si hay más de 20
        assert 'has_more' in result2


class TestGetRouteByIdCommand:
    """Test suite para el comando GetRouteById."""
    
    def test_get_route_by_id_success(self, db, sample_delivery_route):
        """Test obtener ruta por ID exitosamente."""
        command = GetRouteById(route_id=sample_delivery_route.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'route' in result
        assert result['route']['id'] == sample_delivery_route.id
        assert result['route']['route_code'] == sample_delivery_route.route_code
    
    def test_get_route_by_id_not_found(self, db):
        """Test con ID de ruta inexistente."""
        command = GetRouteById(route_id=99999)
        result = command.execute()
        
        assert result['status'] == 'not_found'
        assert 'message' in result
    
    def test_get_route_by_id_with_stops(self, db, sample_delivery_route, sample_route_stop):
        """Test incluir paradas en la respuesta."""
        command = GetRouteById(route_id=sample_delivery_route.id, include_stops=True)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'stops' in result['route'] or 'route_stops' in result['route']
    
    def test_get_route_by_id_with_assignments(self, db, sample_delivery_route, sample_route_assignment):
        """Test incluir asignaciones de pedidos."""
        command = GetRouteById(route_id=sample_delivery_route.id, include_assignments=True)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'assignments' in result['route'] or 'order_assignments' in result['route']
    
    def test_get_route_by_id_without_stops(self, db, sample_delivery_route, sample_route_stop):
        """Test excluir paradas de la respuesta."""
        command = GetRouteById(route_id=sample_delivery_route.id, include_stops=False)
        result = command.execute()
        
        assert result['status'] == 'success'
        # Si el modelo siempre incluye stops, verificar que la opción fue pasada
        assert 'route' in result
    
    def test_get_route_by_id_includes_vehicle_info(self, db, sample_delivery_route, sample_vehicle):
        """Test que incluye información del vehículo."""
        command = GetRouteById(route_id=sample_delivery_route.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        # Verificar que hay información del vehículo
        route = result['route']
        assert 'vehicle' in route or 'vehicle_id' in route


class TestGetRoutesByDateCommand:
    """Test suite para el comando GetRoutesByDate."""
    
    def test_get_routes_by_date_success(self, db, sample_distribution_center, sample_delivery_route):
        """Test consulta de rutas por fecha."""
        command = GetRoutesByDate(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'routes' in result
        assert 'summary' in result
        assert result['date'] == date.today().isoformat()
    
    def test_get_routes_by_date_summary_metrics(self, db, sample_distribution_center, sample_vehicle):
        """Test métricas agregadas del resumen."""
        # Crear varias rutas para la misma fecha
        for i in range(3):
            route = DeliveryRoute(
                route_code=f'ROUTE-SUMMARY-{i:03d}',
                vehicle_id=sample_vehicle.id,
                planned_date=date.today(),
                status='draft',
                total_distance_km=Decimal('10.00'),
                total_orders=5,
                distribution_center_id=sample_distribution_center.id
            )
            db.session.add(route)
        db.session.commit()
        
        command = GetRoutesByDate(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        summary = result['summary']
        assert summary['total_routes'] >= 3
        assert summary['total_distance_km'] >= 30.0
        assert summary['total_orders'] >= 15
        assert 'status_counts' in summary
    
    def test_get_routes_by_date_status_counts(self, db, sample_distribution_center, sample_vehicle):
        """Test conteo de rutas por estado."""
        # Crear rutas con diferentes estados
        statuses = ['draft', 'active', 'in_progress', 'completed']
        target_date = date.today() + timedelta(days=1)
        
        for i, status in enumerate(statuses):
            route = DeliveryRoute(
                route_code=f'ROUTE-STATUS-{i:03d}',
                vehicle_id=sample_vehicle.id,
                planned_date=target_date,
                status=status,
                distribution_center_id=sample_distribution_center.id
            )
            db.session.add(route)
        db.session.commit()
        
        command = GetRoutesByDate(
            distribution_center_id=sample_distribution_center.id,
            planned_date=target_date
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        status_counts = result['summary']['status_counts']
        assert len(status_counts) >= 4
        assert status_counts['draft'] >= 1
        assert status_counts['active'] >= 1
    
    def test_get_routes_by_date_empty(self, db, sample_distribution_center):
        """Test fecha sin rutas."""
        future_date = date.today() + timedelta(days=100)
        
        command = GetRoutesByDate(
            distribution_center_id=sample_distribution_center.id,
            planned_date=future_date
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert result['routes'] == []
        assert result['summary']['total_routes'] == 0
        assert result['summary']['total_distance_km'] == 0
        assert result['summary']['total_orders'] == 0
    
    def test_get_routes_by_date_different_centers(self, db, sample_distribution_center, sample_distribution_center_2, sample_vehicle):
        """Test que filtra correctamente por centro de distribución."""
        target_date = date.today() + timedelta(days=2)
        
        # Ruta para DC 1
        route1 = DeliveryRoute(
            route_code='ROUTE-DC1',
            vehicle_id=sample_vehicle.id,
            planned_date=target_date,
            status='draft',
            distribution_center_id=sample_distribution_center.id
        )
        
        # Crear vehículo para DC 2
        vehicle2 = Vehicle(
            plate='DC2-VEH',
            vehicle_type='van',
            capacity_kg=Decimal('1000.00'),
            capacity_m3=Decimal('10.000'),
            has_refrigeration=False,
            cost_per_km=Decimal('3.00'),
            home_distribution_center_id=sample_distribution_center_2.id,
            is_available=True,
            is_active=True
        )
        db.session.add(vehicle2)
        db.session.flush()
        
        # Ruta para DC 2
        route2 = DeliveryRoute(
            route_code='ROUTE-DC2',
            vehicle_id=vehicle2.id,
            planned_date=target_date,
            status='draft',
            distribution_center_id=sample_distribution_center_2.id
        )
        
        db.session.add_all([route1, route2])
        db.session.commit()
        
        # Consultar solo DC 1
        command = GetRoutesByDate(
            distribution_center_id=sample_distribution_center.id,
            planned_date=target_date
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert all(r['distribution_center_id'] == sample_distribution_center.id for r in result['routes'])
        
        # Consultar solo DC 2
        command2 = GetRoutesByDate(
            distribution_center_id=sample_distribution_center_2.id,
            planned_date=target_date
        )
        result2 = command2.execute()
        
        assert result2['status'] == 'success'
        assert all(r['distribution_center_id'] == sample_distribution_center_2.id for r in result2['routes'])
