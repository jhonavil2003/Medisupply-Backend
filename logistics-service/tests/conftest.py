import pytest
import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.main import create_app
from src.session import db as _db
from src.models.inventory import Inventory
from src.models.distribution_center import DistributionCenter
from src.models.warehouse_location import WarehouseLocation
from src.models.product_batch import ProductBatch
from src.models.vehicle import Vehicle
from src.models.delivery_route import DeliveryRoute
from src.models.route_stop import RouteStop
from src.models.route_assignment import RouteAssignment
from src.models.geocoded_address import GeocodedAddress


@pytest.fixture(scope='function')
def app():
    config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    }
    
    app_obj = create_app(config=config)
    if isinstance(app_obj, tuple):
        app = app_obj[0]
    else:
        app = app_obj
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope='function')
def db(app):
    with app.app_context():
        yield _db


@pytest.fixture(scope='function')
def client(app):
    return app.test_client()


@pytest.fixture
def sample_distribution_center(db):
    dc = DistributionCenter(
        code='DC-001',
        name='Centro Bogotá',
        city='Bogotá',
        country='Colombia',
        is_active=True,
        supports_cold_chain=True,
        latitude=Decimal('4.60971'),
        longitude=Decimal('-74.08175')
    )
    db.session.add(dc)
    db.session.commit()
    return dc


@pytest.fixture
def sample_distribution_center_2(db):
    dc = DistributionCenter(
        code='DC-002',
        name='Centro Medellín',
        city='Medellín',
        country='Colombia',
        is_active=True,
        supports_cold_chain=False
    )
    db.session.add(dc)
    db.session.commit()
    return dc


@pytest.fixture
def sample_inventory(db, sample_distribution_center):
    inventory = Inventory(
        product_sku='JER-001',
        distribution_center_id=sample_distribution_center.id,
        quantity_available=100,
        quantity_reserved=10,
        quantity_in_transit=5,
        minimum_stock_level=20,
        unit_cost=Decimal('2.50')
    )
    db.session.add(inventory)
    db.session.commit()
    return inventory


@pytest.fixture
def multiple_inventory_items(db, sample_distribution_center, sample_distribution_center_2):
    items = [
        Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=100,
            quantity_reserved=10,
            quantity_in_transit=5,
            minimum_stock_level=20
        ),
        Inventory(
            product_sku='JER-001',
            distribution_center_id=sample_distribution_center_2.id,
            quantity_available=50,
            quantity_reserved=5,
            quantity_in_transit=0,
            minimum_stock_level=20
        ),
        Inventory(
            product_sku='VAC-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=30,
            quantity_reserved=0,
            quantity_in_transit=10,
            minimum_stock_level=10
        ),
        Inventory(
            product_sku='GUANTE-001',
            distribution_center_id=sample_distribution_center.id,
            quantity_available=0,
            quantity_reserved=0,
            quantity_in_transit=0,
            minimum_stock_level=50
        )
    ]
    
    for item in items:
        db.session.add(item)
    
    db.session.commit()
    return items


@pytest.fixture
def db_session(db):
    """Alias para el fixture db, usado en los tests"""
    return db.session


@pytest.fixture
def distribution_center(db, sample_distribution_center):
    """Alias para sample_distribution_center"""
    return sample_distribution_center


@pytest.fixture
def warehouse_location(db, sample_distribution_center):
    """Fixture para una ubicación de bodega"""
    location = WarehouseLocation(
        distribution_center_id=sample_distribution_center.id,
        zone_type='refrigerated',
        aisle='A',
        shelf='E1',
        level_position='N1-P1',
        temperature_min=2.0,
        temperature_max=8.0,
        current_temperature=5.0,
        capacity_units=100,
        is_active=True
    )
    db.session.add(location)
    db.session.commit()
    return location


@pytest.fixture
def warehouse_location_ambient(db, sample_distribution_center):
    """Fixture para una ubicación de bodega ambiente"""
    location = WarehouseLocation(
        distribution_center_id=sample_distribution_center.id,
        zone_type='ambient',
        aisle='B',
        shelf='E2',
        level_position='N2-P1',
        capacity_units=200,
        is_active=True
    )
    db.session.add(location)
    db.session.commit()
    return location


# ==================== FIXTURES PARA RUTAS Y VEHÍCULOS ====================

@pytest.fixture
def sample_vehicle(db, sample_distribution_center):
    """Fixture para un vehículo de prueba con refrigeración"""
    vehicle = Vehicle(
        plate='ABC-123',
        vehicle_type='refrigerated_truck',
        brand='Chevrolet',
        model='NPR',
        year=2022,
        capacity_kg=Decimal('2500.00'),
        capacity_m3=Decimal('15.000'),
        has_refrigeration=True,
        temperature_min=Decimal('2.00'),
        temperature_max=Decimal('8.00'),
        max_stops_per_route=15,
        avg_speed_kmh=Decimal('40.00'),
        cost_per_km=Decimal('3.50'),
        home_distribution_center_id=sample_distribution_center.id,
        driver_name='Carlos Pérez',
        driver_phone='+57 300 1234567',
        driver_license='12345678',
        is_available=True,
        is_active=True
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


@pytest.fixture
def sample_vehicle_no_refrigeration(db, sample_distribution_center):
    """Fixture para un vehículo sin refrigeración"""
    vehicle = Vehicle(
        plate='XYZ-789',
        vehicle_type='van',
        brand='Ford',
        model='Transit',
        year=2021,
        capacity_kg=Decimal('1200.00'),
        capacity_m3=Decimal('10.000'),
        has_refrigeration=False,
        max_stops_per_route=12,
        avg_speed_kmh=Decimal('45.00'),
        cost_per_km=Decimal('2.80'),
        home_distribution_center_id=sample_distribution_center.id,
        driver_name='María González',
        driver_phone='+57 310 9876543',
        driver_license='87654321',
        is_available=True,
        is_active=True
    )
    db.session.add(vehicle)
    db.session.commit()
    return vehicle


@pytest.fixture
def sample_delivery_route(db, sample_vehicle, sample_distribution_center):
    """Fixture para una ruta de entrega"""
    route = DeliveryRoute(
        route_code='ROUTE-TEST-001',
        vehicle_id=sample_vehicle.id,
        driver_name=sample_vehicle.driver_name,
        driver_phone=sample_vehicle.driver_phone,
        planned_date=date.today(),
        status='draft',
        total_distance_km=Decimal('25.50'),
        estimated_duration_minutes=180,
        total_orders=5,
        total_stops=5,
        total_weight_kg=Decimal('250.00'),
        total_volume_m3=Decimal('2.500'),
        optimization_score=Decimal('85.50'),
        optimization_strategy='balanced',
        has_cold_chain_products=True,
        distribution_center_id=sample_distribution_center.id,
        created_by='test_user'
    )
    db.session.add(route)
    db.session.commit()
    return route


@pytest.fixture
def sample_route_stop(db, sample_delivery_route):
    """Fixture para una parada de ruta"""
    stop = RouteStop(
        route_id=sample_delivery_route.id,
        sequence_order=1,
        customer_name='Hospital Test',
        delivery_address='Calle 100 # 50-25',
        city='Bogotá',
        department='Cundinamarca',
        latitude=Decimal('4.68682'),
        longitude=Decimal('-74.05477'),
        estimated_arrival_time=datetime.utcnow(),
        estimated_service_time_minutes=30,
        stop_type='delivery',
        status='pending'
    )
    db.session.add(stop)
    db.session.commit()
    return stop


@pytest.fixture
def sample_route_assignment(db, sample_delivery_route, sample_route_stop):
    """Fixture para una asignación de pedido a ruta"""
    assignment = RouteAssignment(
        route_id=sample_delivery_route.id,
        stop_id=sample_route_stop.id,
        order_id=1001,
        order_number='ORD-2025-001',
        customer_name='Hospital Test',
        customer_type='hospital',
        delivery_address='Calle 100 # 50-25',
        clinical_priority=2,
        requires_cold_chain=True,
        total_weight_kg=Decimal('50.00'),
        total_volume_m3=Decimal('0.500'),
        total_items_count=10,
        status='assigned',
        created_by='test_user'
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment


@pytest.fixture
def sample_geocoded_address(db):
    """Fixture para una dirección geocodificada en caché"""
    geocoded = GeocodedAddress(
        address_hash='test_hash_123',
        original_address='Calle 100 # 50-25, Bogotá',
        formatted_address='Cl. 100 #50-25, Bogotá, Colombia',
        latitude=Decimal('4.68682'),
        longitude=Decimal('-74.05477'),
        geocoding_confidence='high',
        provider='google_maps',
        geocoded_at=datetime.utcnow(),
        times_used=1
    )
    db.session.add(geocoded)
    db.session.commit()
    return geocoded


@pytest.fixture
def multiple_vehicles(db, sample_distribution_center, sample_distribution_center_2):
    """Fixture para múltiples vehículos con diferentes capacidades"""
    vehicles = [
        Vehicle(
            plate='AAA-111',
            vehicle_type='refrigerated_truck',
            brand='Hino',
            model='Serie 300',
            capacity_kg=Decimal('3000.00'),
            capacity_m3=Decimal('18.000'),
            has_refrigeration=True,
            temperature_min=Decimal('2.00'),
            temperature_max=Decimal('8.00'),
            cost_per_km=Decimal('4.00'),
            home_distribution_center_id=sample_distribution_center.id,
            is_available=True,
            is_active=True
        ),
        Vehicle(
            plate='BBB-222',
            vehicle_type='van',
            brand='Nissan',
            model='Urvan',
            capacity_kg=Decimal('1000.00'),
            capacity_m3=Decimal('8.000'),
            has_refrigeration=False,
            cost_per_km=Decimal('2.50'),
            home_distribution_center_id=sample_distribution_center.id,
            is_available=True,
            is_active=True
        ),
        Vehicle(
            plate='CCC-333',
            vehicle_type='truck',
            brand='Isuzu',
            model='NQR',
            capacity_kg=Decimal('4000.00'),
            capacity_m3=Decimal('25.000'),
            has_refrigeration=False,
            cost_per_km=Decimal('5.00'),
            home_distribution_center_id=sample_distribution_center_2.id,
            is_available=False,  # No disponible
            is_active=True
        )
    ]
    for vehicle in vehicles:
        db.session.add(vehicle)
    db.session.commit()
    return vehicles


@pytest.fixture
def socketio_client(app):
    """Fixture para cliente de Socket.IO en tests."""
    from flask_socketio import SocketIOTestClient
    from src.websockets.websocket_manager import socketio
    
    if socketio:
        return socketio.test_client(app)
    return None
