"""
Tests unitarios para los comandos de gestión de vehículos.
Basado en la estructura de tests del proyecto.
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.commands.get_vehicles import (
    GetVehicles, 
    GetVehicleById, 
    UpdateVehicleAvailability,
    GetAvailableVehicles
)
from src.models.vehicle import Vehicle
from src.models.delivery_route import DeliveryRoute


class TestGetVehiclesCommand:
    """Test suite para el comando GetVehicles."""
    
    def test_get_vehicles_all(self, db, sample_vehicle):
        """Test consulta de todos los vehículos."""
        command = GetVehicles()
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'vehicles' in result
        assert len(result['vehicles']) >= 1
        assert 'statistics' in result
    
    def test_get_vehicles_by_distribution_center(self, db, sample_distribution_center, sample_vehicle):
        """Test filtrado por centro de distribución."""
        command = GetVehicles(distribution_center_id=sample_distribution_center.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert all(
            v['home_distribution_center_id'] == sample_distribution_center.id 
            for v in result['vehicles']
        )
    
    def test_get_vehicles_by_availability(self, db, sample_vehicle, sample_vehicle_no_refrigeration):
        """Test filtrado por disponibilidad."""
        # Marcar un vehículo como no disponible
        sample_vehicle_no_refrigeration.is_available = False
        db.session.commit()
        
        # Consultar solo disponibles
        command = GetVehicles(is_available=True)
        result = command.execute()
        
        assert result['status'] == 'success'
        # Verificar estructura anidada
        assert all(v['status']['is_available'] is True for v in result['vehicles'])
        
        # Consultar solo no disponibles
        command2 = GetVehicles(is_available=False)
        result2 = command2.execute()
        
        assert result2['status'] == 'success'
        assert all(v['status']['is_available'] is False for v in result2['vehicles'])
    
    def test_get_vehicles_by_refrigeration(self, db, sample_vehicle, sample_vehicle_no_refrigeration):
        """Test filtrado por capacidad de refrigeración."""
        # Con refrigeración
        command1 = GetVehicles(has_refrigeration=True)
        result1 = command1.execute()
        
        assert result1['status'] == 'success'
        # Verificar estructura anidada features
        assert all(v['features']['has_refrigeration'] is True for v in result1['vehicles'])
        
        # Sin refrigeración
        command2 = GetVehicles(has_refrigeration=False)
        result2 = command2.execute()
        
        assert result2['status'] == 'success'
        assert all(v['features']['has_refrigeration'] is False for v in result2['vehicles'])
    
    def test_get_vehicles_by_type(self, db, sample_vehicle):
        """Test filtrado por tipo de vehículo."""
        command = GetVehicles(vehicle_type='refrigerated_truck')
        result = command.execute()
        
        assert result['status'] == 'success'
        assert all(v['vehicle_type'] == 'refrigerated_truck' for v in result['vehicles'])
    
    def test_get_vehicles_statistics(self, db, multiple_vehicles):
        """Test estadísticas de vehículos."""
        command = GetVehicles()
        result = command.execute()
        
        assert result['status'] == 'success'
        stats = result['statistics']
        
        assert 'total_vehicles' in stats
        assert 'available' in stats
        assert 'unavailable' in stats
        assert 'with_refrigeration' in stats
        assert 'total_capacity_kg' in stats
        assert 'total_capacity_m3' in stats
        
        assert stats['total_vehicles'] == stats['available'] + stats['unavailable']
    
    def test_get_vehicles_multiple_filters(self, db, sample_distribution_center, sample_vehicle):
        """Test múltiples filtros combinados."""
        command = GetVehicles(
            distribution_center_id=sample_distribution_center.id,
            is_available=True,
            has_refrigeration=True
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        for vehicle in result['vehicles']:
            assert vehicle['home_distribution_center_id'] == sample_distribution_center.id
            # Verificar estructura anidada
            assert vehicle['status']['is_available'] is True
            assert vehicle['features']['has_refrigeration'] is True
    
    def test_get_vehicles_empty_result(self, db):
        """Test consulta que no retorna resultados."""
        command = GetVehicles(distribution_center_id=99999)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert result['vehicles'] == []
        assert result['statistics']['total_vehicles'] == 0


class TestGetVehicleByIdCommand:
    """Test suite para el comando GetVehicleById."""
    
    def test_get_vehicle_by_id_success(self, db, sample_vehicle):
        """Test obtener vehículo por ID exitosamente."""
        command = GetVehicleById(vehicle_id=sample_vehicle.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'vehicle' in result
        assert result['vehicle']['id'] == sample_vehicle.id
        assert result['vehicle']['plate'] == sample_vehicle.plate
    
    def test_get_vehicle_by_id_not_found(self, db):
        """Test con ID de vehículo inexistente."""
        command = GetVehicleById(vehicle_id=99999)
        result = command.execute()
        
        assert result['status'] == 'not_found'
        assert 'message' in result
    
    def test_get_vehicle_by_id_includes_distribution_center(self, db, sample_vehicle, sample_distribution_center):
        """Test que incluye información del centro de distribución."""
        command = GetVehicleById(vehicle_id=sample_vehicle.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        vehicle = result['vehicle']
        assert 'distribution_center' in vehicle or 'home_distribution_center_id' in vehicle
    
    def test_get_vehicle_by_id_complete_info(self, db, sample_vehicle):
        """Test que retorna información completa del vehículo."""
        command = GetVehicleById(vehicle_id=sample_vehicle.id)
        result = command.execute()
        
        assert result['status'] == 'success'
        vehicle = result['vehicle']
        
        # Verificar campos importantes
        assert 'plate' in vehicle
        assert 'vehicle_type' in vehicle
        # Verificar estructura anidada
        assert 'capacity' in vehicle
        assert 'kg' in vehicle['capacity']
        assert 'm3' in vehicle['capacity']
        # Verificar features anidadas
        assert 'features' in vehicle
        assert 'has_refrigeration' in vehicle['features']
        assert 'driver' in vehicle
        assert 'driver_name' in vehicle['driver'] or 'name' in vehicle['driver']


class TestUpdateVehicleAvailabilityCommand:
    """Test suite para el comando UpdateVehicleAvailability."""
    
    def test_update_vehicle_availability_to_unavailable(self, db, sample_vehicle):
        """Test marcar vehículo como no disponible."""
        assert sample_vehicle.is_available is True
        
        command = UpdateVehicleAvailability(
            vehicle_id=sample_vehicle.id,
            is_available=False,
            reason='Mantenimiento programado'
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'message' in result
        
        # Verificar cambio en BD
        db.session.refresh(sample_vehicle)
        assert sample_vehicle.is_available is False
    
    def test_update_vehicle_availability_to_available(self, db, sample_vehicle):
        """Test marcar vehículo como disponible."""
        # Primero marcarlo como no disponible
        sample_vehicle.is_available = False
        db.session.commit()
        
        command = UpdateVehicleAvailability(
            vehicle_id=sample_vehicle.id,
            is_available=True,
            reason='Mantenimiento completado'
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        
        # Verificar cambio en BD
        db.session.refresh(sample_vehicle)
        assert sample_vehicle.is_available is True
    
    def test_update_vehicle_availability_without_reason(self, db, sample_vehicle):
        """Test actualización sin especificar motivo."""
        command = UpdateVehicleAvailability(
            vehicle_id=sample_vehicle.id,
            is_available=False
        )
        result = command.execute()
        
        assert result['status'] == 'success'
    
    def test_update_vehicle_availability_not_found(self, db):
        """Test con vehículo inexistente."""
        command = UpdateVehicleAvailability(
            vehicle_id=99999,
            is_available=False
        )
        result = command.execute()
        
        assert result['status'] == 'not_found'
        assert 'message' in result
    
    def test_update_vehicle_availability_returns_vehicle_data(self, db, sample_vehicle):
        """Test que retorna datos actualizados del vehículo."""
        command = UpdateVehicleAvailability(
            vehicle_id=sample_vehicle.id,
            is_available=False
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'vehicle' in result
        # Verificar estructura anidada
        assert result['vehicle']['status']['is_available'] is False


class TestGetAvailableVehiclesCommand:
    """Test suite para el comando GetAvailableVehicles."""
    
    def test_get_available_vehicles_success(self, db, sample_distribution_center, sample_vehicle):
        """Test obtener vehículos disponibles."""
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert 'vehicles' in result
        assert 'summary' in result
        assert result['distribution_center_id'] == sample_distribution_center.id
    
    def test_get_available_vehicles_excludes_unavailable(self, db, sample_distribution_center, sample_vehicle):
        """Test que excluye vehículos marcados como no disponibles."""
        # Marcar vehículo como no disponible
        sample_vehicle.is_available = False
        db.session.commit()
        
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        # No debería incluir el vehículo no disponible
        vehicle_ids = [v['id'] for v in result['vehicles']]
        assert sample_vehicle.id not in vehicle_ids
    
    def test_get_available_vehicles_excludes_with_active_routes(self, db, sample_distribution_center, sample_vehicle):
        """Test que excluye vehículos con rutas activas."""
        target_date = date.today() + timedelta(days=1)
        
        # Crear ruta activa para el vehículo
        route = DeliveryRoute(
            route_code='ROUTE-ACTIVE-TEST',
            vehicle_id=sample_vehicle.id,
            planned_date=target_date,
            status='active',
            distribution_center_id=sample_distribution_center.id
        )
        db.session.add(route)
        db.session.commit()
        
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=target_date
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        vehicle_ids = [v['id'] for v in result['vehicles']]
        # No debería incluir el vehículo con ruta activa
        assert sample_vehicle.id not in vehicle_ids
    
    def test_get_available_vehicles_includes_with_completed_routes(self, db, sample_distribution_center, sample_vehicle):
        """Test que incluye vehículos con rutas completadas."""
        target_date = date.today() + timedelta(days=2)
        
        # Crear ruta completada para el vehículo
        route = DeliveryRoute(
            route_code='ROUTE-COMPLETED-TEST',
            vehicle_id=sample_vehicle.id,
            planned_date=target_date,
            status='completed',
            distribution_center_id=sample_distribution_center.id
        )
        db.session.add(route)
        db.session.commit()
        
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=target_date
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        vehicle_ids = [v['id'] for v in result['vehicles']]
        # Debería incluir el vehículo (ruta completada)
        assert sample_vehicle.id in vehicle_ids
    
    def test_get_available_vehicles_summary(self, db, sample_distribution_center, multiple_vehicles):
        """Test resumen de capacidades disponibles."""
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        summary = result['summary']
        
        assert 'total_available' in summary
        assert 'with_refrigeration' in summary
        assert 'total_capacity_kg' in summary
        assert 'total_capacity_m3' in summary
        
        assert summary['total_available'] >= 0
        assert summary['total_capacity_kg'] >= 0
        assert summary['total_capacity_m3'] >= 0
    
    def test_get_available_vehicles_different_dates(self, db, sample_distribution_center, sample_vehicle):
        """Test disponibilidad para diferentes fechas."""
        # Crear ruta para mañana
        tomorrow = date.today() + timedelta(days=1)
        route = DeliveryRoute(
            route_code='ROUTE-TOMORROW',
            vehicle_id=sample_vehicle.id,
            planned_date=tomorrow,
            status='active',
            distribution_center_id=sample_distribution_center.id
        )
        db.session.add(route)
        db.session.commit()
        
        # Consultar disponibilidad para hoy (debería estar disponible)
        command_today = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result_today = command_today.execute()
        
        vehicle_ids_today = [v['id'] for v in result_today['vehicles']]
        assert sample_vehicle.id in vehicle_ids_today
        
        # Consultar disponibilidad para mañana (no debería estar disponible)
        command_tomorrow = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=tomorrow
        )
        result_tomorrow = command_tomorrow.execute()
        
        vehicle_ids_tomorrow = [v['id'] for v in result_tomorrow['vehicles']]
        assert sample_vehicle.id not in vehicle_ids_tomorrow
    
    def test_get_available_vehicles_default_date(self, db, sample_distribution_center, sample_vehicle):
        """Test que usa fecha actual por defecto."""
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert result['date'] == date.today().isoformat()
    
    def test_get_available_vehicles_empty_result(self, db, sample_distribution_center, sample_vehicle):
        """Test cuando no hay vehículos disponibles."""
        # Marcar todos los vehículos como no disponibles
        sample_vehicle.is_available = False
        db.session.commit()
        
        command = GetAvailableVehicles(
            distribution_center_id=sample_distribution_center.id,
            planned_date=date.today()
        )
        result = command.execute()
        
        assert result['status'] == 'success'
        assert result['vehicles'] == []
        assert result['summary']['total_available'] == 0
