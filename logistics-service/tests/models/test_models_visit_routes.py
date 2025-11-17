"""
Tests unitarios para los modelos VisitRoute y VisitRouteStop.
"""

import pytest
from datetime import date, datetime, time, timedelta
from src.models.visit_route import VisitRoute, VisitRouteStatus
from src.models.visit_route_stop import VisitRouteStop


class TestVisitRouteModel:
    """Tests para el modelo VisitRoute"""
    
    def test_create_visit_route(self, db_session):
        """Test: Crear una ruta de visitas básica"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT,
            optimization_strategy="minimize_distance"
        )
        
        db_session.add(route)
        db_session.commit()
        
        assert route.id is not None
        assert route.route_code == "VISIT-20251120-S001-001"
        assert route.salesperson_id == 1
        assert route.status == VisitRouteStatus.DRAFT
        assert route.created_at is not None
    
    def test_generate_route_code(self, app):
        """Test: Generar código de ruta automáticamente"""
        with app.app_context():
            route_code = VisitRoute.generate_route_code(
                salesperson_id=2,
                planned_date=date(2025, 11, 20)
            )
            
            assert route_code.startswith("VISIT-20251120-S002-")
            assert len(route_code) == 23  # VISIT-YYYYMMDD-SXXX-XXX
    
    def test_visit_route_to_dict(self, db_session):
        """Test: Serializar ruta a diccionario"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT,
            total_stops=3,
            total_distance_km=25.5,
            estimated_duration_minutes=150
        )
        
        db_session.add(route)
        db_session.commit()
        
        route_dict = route.to_dict()
        
        assert route_dict['id'] == route.id
        assert route_dict['route_code'] == "VISIT-20251120-S001-001"
        assert route_dict['status'] == 'draft'
        assert route_dict['salesperson']['id'] == 1
        assert route_dict['salesperson']['name'] == "Juan Pérez"
        assert route_dict['metrics']['total_stops'] == 3
        assert route_dict['metrics']['total_distance_km'] == 25.5
    
    def test_confirm_route(self, db_session):
        """Test: Confirmar una ruta en estado DRAFT"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        route.confirm()
        db_session.commit()
        
        assert route.status == VisitRouteStatus.CONFIRMED
        assert route.confirmed_at is not None
    
    def test_start_route(self, db_session):
        """Test: Iniciar una ruta confirmada"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.CONFIRMED
        )
        
        db_session.add(route)
        db_session.commit()
        
        route.start()
        db_session.commit()
        
        assert route.status == VisitRouteStatus.IN_PROGRESS
        assert route.started_at is not None
    
    def test_start_route_not_confirmed_raises_error(self, db_session):
        """Test: No se puede iniciar una ruta que no está confirmada"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        with pytest.raises(ValueError, match="Solo se pueden iniciar rutas confirmadas"):
            route.start()
    
    def test_complete_route(self, db_session):
        """Test: Completar una ruta en progreso"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        db_session.add(route)
        db_session.commit()
        
        route.complete()
        db_session.commit()
        
        assert route.status == VisitRouteStatus.COMPLETED
        assert route.completed_at is not None
    
    def test_complete_route_not_in_progress_raises_error(self, db_session):
        """Test: No se puede completar una ruta que no está en progreso"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        with pytest.raises(ValueError, match="Solo se pueden completar rutas en progreso"):
            route.complete()
    
    def test_cancel_route(self, db_session):
        """Test: Cancelar una ruta en estado DRAFT o CONFIRMED"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.CONFIRMED
        )
        
        db_session.add(route)
        db_session.commit()
        
        route.cancel()
        db_session.commit()
        
        assert route.status == VisitRouteStatus.CANCELLED
    
    def test_cannot_cancel_completed_route(self, db_session):
        """Test: No se puede cancelar una ruta completada"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.COMPLETED
        )
        
        db_session.add(route)
        db_session.commit()
        
        with pytest.raises(ValueError, match="No se puede cancelar una ruta"):
            route.cancel()
    
    def test_update_metrics(self, db_session):
        """Test: Actualizar métricas de la ruta basándose en las paradas"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        # Agregar paradas
        stop1 = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=1,
            customer_name="Cliente 1",
            latitude=4.6486259,
            longitude=-74.0628451,
            distance_from_previous_km=5.0,
            estimated_service_time_minutes=30
        )
        stop2 = VisitRouteStop(
            route_id=route.id,
            sequence_order=2,
            customer_id=2,
            customer_name="Cliente 2",
            latitude=4.7040381,
            longitude=-74.0314636,
            distance_from_previous_km=7.5,
            estimated_service_time_minutes=30
        )
        
        db_session.add_all([stop1, stop2])
        db_session.commit()
        
        route.update_metrics()
        db_session.commit()
        
        assert route.total_stops == 2
        assert route.total_distance_km == 12.5
        assert route.estimated_duration_minutes == 60
    
    def test_generate_google_maps_url(self, db_session):
        """Test: Generar URL de Google Maps con waypoints"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT,
            start_latitude=4.6097,
            start_longitude=-74.0817
        )
        
        db_session.add(route)
        db_session.commit()
        
        # Agregar paradas
        stop1 = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=1,
            customer_name="Cliente 1",
            latitude=4.6486259,
            longitude=-74.0628451
        )
        stop2 = VisitRouteStop(
            route_id=route.id,
            sequence_order=2,
            customer_id=2,
            customer_name="Cliente 2",
            latitude=4.7040381,
            longitude=-74.0314636
        )
        
        db_session.add_all([stop1, stop2])
        db_session.commit()
        
        map_url = route.generate_google_maps_url()
        
        assert "maps.google.com/maps/dir/" in map_url
        assert "origin=4.60970000,-74.08170000" in map_url
        assert "waypoints=" in map_url
        assert "4.64862590" in map_url
        assert "-74.06284510" in map_url


class TestVisitRouteStopModel:
    """Tests para el modelo VisitRouteStop"""
    
    def test_create_visit_route_stop(self, db_session):
        """Test: Crear una parada de visita"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            customer_document="900123456-1",
            address="Calle 50 #20-30",
            city="Bogotá",
            latitude=4.6486259,
            longitude=-74.0628451,
            contact_name="Juan Pérez",
            contact_phone="3001234567",
            estimated_arrival_time=datetime(2025, 11, 20, 9, 0),
            estimated_departure_time=datetime(2025, 11, 20, 9, 30),
            estimated_service_time_minutes=30,
            distance_from_previous_km=5.2,
            travel_time_from_previous_minutes=15
        )
        
        db_session.add(stop)
        db_session.commit()
        
        assert stop.id is not None
        assert stop.route_id == route.id
        assert stop.sequence_order == 1
        assert stop.customer_name == "Farmacia San Rafael"
        assert stop.is_completed is False
        assert stop.is_skipped is False
    
    def test_visit_route_stop_to_dict(self, db_session):
        """Test: Serializar parada a diccionario"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            latitude=4.6486259,
            longitude=-74.0628451,
            estimated_service_time_minutes=30
        )
        
        db_session.add(stop)
        db_session.commit()
        
        stop_dict = stop.to_dict()
        
        assert stop_dict['id'] == stop.id
        assert stop_dict['sequence_order'] == 1
        assert stop_dict['customer']['id'] == 123
        assert stop_dict['customer']['name'] == "Farmacia San Rafael"
        assert stop_dict['location']['latitude'] == 4.6486259
        assert stop_dict['status']['is_completed'] is False
    
    def test_complete_stop(self, db_session):
        """Test: Completar una parada"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.IN_PROGRESS
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            latitude=4.6486259,
            longitude=-74.0628451,
            estimated_arrival_time=datetime(2025, 11, 20, 9, 0)
        )
        
        db_session.add(stop)
        db_session.commit()
        
        arrival = datetime(2025, 11, 20, 9, 5)
        departure = datetime(2025, 11, 20, 9, 40)
        notes = "Cliente satisfecho"
        
        stop.complete(arrival, departure, notes)
        db_session.commit()
        
        assert stop.is_completed is True
        assert stop.actual_arrival_time == arrival
        assert stop.actual_departure_time == departure
        assert stop.visit_notes == notes  # El método guarda en visit_notes, no notes
        assert stop.completed_at is not None
    
    def test_skip_stop(self, db_session):
        """Test: Omitir una parada"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.IN_PROGRESS
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            latitude=4.6486259,
            longitude=-74.0628451
        )
        
        db_session.add(stop)
        db_session.commit()
        
        reason = "Cliente cerrado"
        
        stop.skip(reason)
        db_session.commit()
        
        assert stop.is_skipped is True
        assert stop.skip_reason == reason
        assert stop.completed_at is not None  # El método skip() usa completed_at
    
    def test_get_google_maps_link(self, db_session):
        """Test: Generar link de Google Maps para la parada"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            latitude=4.6486259,
            longitude=-74.0628451
        )
        
        db_session.add(stop)
        db_session.commit()
        
        maps_link = stop.get_google_maps_link()
        
        assert "maps.google.com" in maps_link
        assert "4.6486259" in maps_link
        assert "-74.0628451" in maps_link
    
    def test_estimated_duration_total_minutes(self, db_session):
        """Test: Calcular duración total estimada (viaje + servicio)"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.DRAFT
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=2,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            latitude=4.6486259,
            longitude=-74.0628451,
            travel_time_from_previous_minutes=15,
            estimated_service_time_minutes=30
        )
        
        db_session.add(stop)
        db_session.commit()
        
        assert stop.estimated_duration_total_minutes == 45
    
    def test_actual_duration_total_minutes(self, db_session):
        """Test: Calcular duración total real"""
        route = VisitRoute(
            route_code="VISIT-20251120-S001-001",
            salesperson_id=1,
            salesperson_name="Juan Pérez",
            salesperson_employee_id="SALES-001",
            planned_date=date(2025, 11, 20),
            status=VisitRouteStatus.IN_PROGRESS
        )
        
        db_session.add(route)
        db_session.commit()
        
        stop = VisitRouteStop(
            route_id=route.id,
            sequence_order=1,
            customer_id=123,
            customer_name="Farmacia San Rafael",
            latitude=4.6486259,
            longitude=-74.0628451
        )
        
        db_session.add(stop)
        db_session.commit()
        
        arrival = datetime(2025, 11, 20, 9, 0)
        departure = datetime(2025, 11, 20, 9, 35)
        
        stop.complete(arrival, departure, "OK")
        db_session.commit()
        
        assert stop.actual_duration_total_minutes == 35
